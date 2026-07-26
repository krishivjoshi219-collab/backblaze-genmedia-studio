import os
import json
import logging
import graphviz
import streamlit as st
from services.security import ProvenanceEngine

logger = logging.getLogger("GenMediaLineageService")
provenance_engine = ProvenanceEngine()

def build_lineage_graph(run_data: dict) -> graphviz.Digraph:
    """
    Constructs a visual pipeline execution tree tracing ancestry:
    [Master Prompt] -> [Refinement Loop Iterations] -> [Generated Assets (PNG/WAV)] -> [Subtitle Manifest] -> [Backblaze B2 Vault Node]
    """
    dot = graphviz.Digraph(comment="GenMedia Asset Lineage Tree", format="svg")
    dot.attr(
        bgcolor="#0e1117",
        rankdir="LR",
        splines="polyline",
        nodesep="0.4",
        ranksep="0.7",
        fontname="Space Grotesk, sans-serif"
    )
    dot.attr("node", fontname="Space Grotesk, sans-serif", fontsize="10", style="filled,rounded")
    dot.attr("edge", fontname="Outfit, sans-serif", fontsize="8", color="#a033ff", penwidth="1.5")

    # 1. Master Prompt Node
    master_prompt = run_data.get("master_prompt") or run_data.get("prompt") or "Master Prompt / Story Concept"
    if len(master_prompt) > 40:
        master_label = master_prompt[:38] + "..."
    else:
        master_label = master_prompt

    dot.node(
        "master_prompt",
        f"Master Prompt\n[{master_label}]",
        fillcolor="#1e293b",
        fontcolor="#f8fafc",
        shape="box",
        color="#38bdf8"
    )

    # 2. Refinement Loop Iteration Nodes
    iterations = run_data.get("iterations", [])
    last_iter_node = "master_prompt"

    if iterations:
        for idx, iter_data in enumerate(iterations):
            iter_id = f"iteration_{idx + 1}"
            score = iter_data.get("score", 0.0)
            passed = iter_data.get("passed", False)
            status_symbol = "PASSED" if passed else "FAILED"
            fill = "#065f46" if passed else "#831843"
            border = "#10b981" if passed else "#ef4444"

            label = f"Refinement Iteration {idx + 1}\nScore: {score:.2f} [{status_symbol}]"
            dot.node(
                iter_id,
                label,
                fillcolor=fill,
                fontcolor="#ffffff",
                shape="box",
                color=border
            )
            dot.edge(last_iter_node, iter_id, label=f"Loop {idx + 1}")
            last_iter_node = iter_id
    else:
        # Single execution node if no iteration loop
        dot.node(
            "pipeline_exec",
            "Pipeline Execution\n[Chained Genblaze Steps]",
            fillcolor="#312e81",
            fontcolor="#ffffff",
            shape="box",
            color="#818cf8"
        )
        dot.edge("master_prompt", "pipeline_exec", label="Execute")
        last_iter_node = "pipeline_exec"

    # 3. Generated Assets (PNG/WAV)
    panels = run_data.get("panels", [])
    asset_nodes = []

    if panels:
        for p in panels:
            p_idx = p.get("panel_index", 0)
            img_path = p.get("image_path")
            aud_path = p.get("audio_path")

            if img_path:
                img_node_id = f"asset_img_{p_idx}"
                img_name = os.path.basename(img_path) if img_path else f"panel_{p_idx}.png"
                dot.node(
                    img_node_id,
                    f"Generated Asset (PNG)\n{img_name}\n[FLUX.1-schnell]",
                    fillcolor="#1e1b4b",
                    fontcolor="#e0e7ff",
                    shape="box",
                    color="#6366f1"
                )
                dot.edge(last_iter_node, img_node_id, label=f"Panel {p_idx + 1} Visual")
                asset_nodes.append(img_node_id)

            if aud_path:
                aud_node_id = f"asset_aud_{p_idx}"
                aud_name = os.path.basename(aud_path) if aud_path else f"track_{p_idx}.wav"
                dot.node(
                    aud_node_id,
                    f"Generated Asset (WAV)\n{aud_name}\n[MusicGen-Small]",
                    fillcolor="#3b0764",
                    fontcolor="#f5d0fe",
                    shape="box",
                    color="#c084fc"
                )
                dot.edge(last_iter_node, aud_node_id, label=f"Panel {p_idx + 1} Audio")
                asset_nodes.append(aud_node_id)
    else:
        # Generic generated asset nodes if panels list is empty
        dot.node(
            "gen_assets",
            "Generated Media Assets\n[PNG Image + WAV Audio]",
            fillcolor="#1e1b4b",
            fontcolor="#e0e7ff",
            shape="box",
            color="#6366f1"
        )
        dot.edge(last_iter_node, "gen_assets", label="Generate")
        asset_nodes.append("gen_assets")

    # 4. Subtitle / Manifest Node
    manifest_hash = run_data.get("manifest_hash", "Canonical SHA-256")
    short_hash = manifest_hash[:16] + "..." if len(manifest_hash) > 16 else manifest_hash

    dot.node(
        "subtitle_manifest",
        f"Subtitle & Run Manifest\nHash: {short_hash}",
        fillcolor="#0f766e",
        fontcolor="#ccfbf1",
        shape="box",
        color="#14b8a6"
    )

    for a_node in asset_nodes:
        dot.edge(a_node, "subtitle_manifest", label="Compile")

    # 5. Backblaze B2 Vault Node
    dot.node(
        "b2_vault_node",
        "Backblaze B2 Vault Node\n[Presigned CDN Stream / Vault]",
        fillcolor="#831843",
        fontcolor="#fce7f3",
        shape="box",
        color="#f43f5e"
    )
    dot.edge("subtitle_manifest", "b2_vault_node", label="Archive")

    return dot

def render_lineage_graph_svg(run_data: dict) -> str:
    """Renders Graphviz SVG string representation of lineage tree."""
    try:
        dot = build_lineage_graph(run_data)
        return dot.pipe(format="svg").decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to generate Graphviz SVG: {e}")
        return ""

def render_lineage_ui(run_data: dict, key_prefix: str = "lineage"):
    """
    Renders an interactive visual expander/card in Streamlit displaying
    the dynamic node lineage graph and C2PA provenance extraction logs.
    """
    st.markdown('<div class="glass-card-neon-purple" style="padding: 1.5rem; margin-top: 1rem;">', unsafe_allow_html=True)
    st.subheader("🌳 Interactive Asset Lineage & Provenance Graph")
    st.write("Dynamic execution ancestry tracing: `[Master Prompt] ➔ [Refinement Loops] ➔ [Generated Assets] ➔ [Subtitle Manifest] ➔ [Backblaze B2 Vault]`")

    # Render Graphviz SVG
    svg_data = render_lineage_graph_svg(run_data)
    if svg_data:
        st.components.v1.html(
            f'<div style="text-align: center; width: 100%; overflow-x: auto; background: #0e1117; padding: 10px; border-radius: 12px;">{svg_data}</div>',
            height=280,
            scrolling=True
        )
    else:
        # Streamlit fallback chart
        try:
            dot = build_lineage_graph(run_data)
            st.graphviz_chart(dot, use_container_width=True)
        except Exception as e:
            st.warning(f"Lineage rendering notice: {e}")

    # Interactive C2PA Provenance Extraction Drawer
    with st.expander("🔐 Inspect C2PA Provenance & Cryptographic Metadata Signatures", expanded=False):
        panels = run_data.get("panels", [])
        extracted_count = 0

        for p in panels:
            p_idx = p.get("panel_index", 0)
            img_p = p.get("image_path")
            aud_p = p.get("audio_path")

            if img_p and os.path.exists(img_p):
                extracted_count += 1
                m, valid, msg = provenance_engine.extract_png_provenance(img_p)
                st.markdown(f"**🖼️ Panel {p_idx + 1} PNG Provenance:**")
                if valid:
                    st.success(f"✅ Verified Signature & Hash: {msg}")
                else:
                    st.info(f"ℹ️ Status: {msg}")
                if m:
                    st.json(m)
                st.markdown("---")

            if aud_p and os.path.exists(aud_p):
                extracted_count += 1
                m, valid, msg = provenance_engine.extract_wav_provenance(aud_p)
                st.markdown(f"**🎧 Panel {p_idx + 1} WAV Provenance:**")
                if valid:
                    st.success(f"✅ Verified Signature & Hash: {msg}")
                else:
                    st.info(f"ℹ️ Status: {msg}")
                if m:
                    st.json(m)
                st.markdown("---")

        if extracted_count == 0:
            st.info("No saved media files available in local path for C2PA chunk extraction. Execute an Agent Studio run to inspect live signatures!")

    st.markdown('</div>', unsafe_allow_html=True)
