import streamlit as st
import requests
import time
import base64
import os

API_URL = "https://grsai.dakka.com.cn/v1/draw/nano-banana"
API_KEY = os.getenv("NANO_BANANA_API_KEY", "")

st.set_page_config(page_title="科研示意图生成器", page_icon="🔬", layout="centered")

st.title("🔬 科研示意图生成器")
st.caption("基于 Nano Banana API")

# API Key 输入
if not API_KEY:
    API_KEY = st.text_input("请输入 API Key", type="password")
    if not API_KEY:
        st.warning("请先输入 API Key 才能使用")
        st.stop()

# 高级 prompt 模板
use_template = st.checkbox("使用高质量模板（推荐）", value=True)

if use_template:
    template_prefix = """Imagine a publication-quality scientific figure that infers the dominant figure type from the provided scientific context (e.g., mechanism, workflow, pathway, or experimental design). The figure should highlight biologically or experimentally central genes, proteins, complexes, domains, cellular compartments, interactions, and relevant parameters (e.g., temperature, time points, MOI, dosage, n), prioritizing clarity and mechanistic coherence while avoiding unsupported or speculative elements. Causal directionality should be explicit, and visual encoding consistent across panels. Apply a colorblind-friendly color logic consistent with Nature-family journals, assigning colors by functional role or biological state and using neutral tones for structural elements. The visual style should benchmark Nature / Cell, with clean professional typography and clear spatial organization. Output on a white background, legible at single-column width, at journal-ready high resolution, with modular panels compatible with Adobe Illustrator.

"""
    st.info("已启用高质量模板，将自动优化为期刊级别的科研示意图")
else:
    template_prefix = ""

# 用户输入
user_prompt = st.text_area("描述你想要的示意图",
    placeholder="例如：一个细胞内的信号转导通路，包含受体、激酶和转录因子",
    height=150)

prompt = template_prefix + user_prompt if use_template else user_prompt

# 参考图上传
uploaded_file = st.file_uploader("上传参考图（可选）", type=["png", "jpg", "jpeg"])
ref_url = None

if uploaded_file:
    file_bytes = uploaded_file.read()
    base64_image = base64.b64encode(file_bytes).decode()
    ref_url = f"data:image/png;base64,{base64_image}"
    st.image(uploaded_file, caption="参考图", width=300)

col1, col2, col3 = st.columns(3)
with col1:
    model = st.selectbox("模型", [
        "nano-banana-fast",
        "nano-banana-2",
        "nano-banana-pro"
    ])
with col2:
    aspect_ratio = st.selectbox("比例", [
        "auto", "1:1", "16:9", "4:3", "3:2"
    ])
with col3:
    image_size = st.selectbox("分辨率", ["1K", "2K", "4K"])

# 生成按钮
if st.button("生成示意图", type="primary"):
    if not user_prompt:
        st.error("请输入描述")
    else:
        with st.spinner("生成中..."):
            payload = {
                "model": model,
                "prompt": prompt,
                "aspectRatio": aspect_ratio,
                "imageSize": image_size,
                "webHook": "-1"
            }

            if ref_url:
                payload["urls"] = [ref_url]

            try:
                response = requests.post(
                    API_URL,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {API_KEY}"
                    },
                    json=payload,
                    timeout=30
                )

                result = response.json()

                if result.get("code") == 0:
                    task_id = result["data"]["id"]
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # 轮询结果
                    max_attempts = 90  # 3 分钟
                    attempt = 0

                    st.info(f"任务ID: {task_id}")

                    while attempt < max_attempts:
                        try:
                            result_response = requests.post(
                                "https://grsai.dakka.com.cn/v1/draw/result",
                                headers={
                                    "Content-Type": "application/json",
                                    "Authorization": f"Bearer {API_KEY}"
                                },
                                json={"id": task_id},
                                timeout=30
                            )
                        except requests.exceptions.Timeout:
                            status_text.text(f"进度: 网络超时，重试中... (尝试 {attempt + 1}/{max_attempts})")
                            time.sleep(2)
                            attempt += 1
                            continue
                        except Exception as e:
                            status_text.text(f"进度: 查询出错 ({str(e)})，重试中...")
                            time.sleep(2)
                            attempt += 1
                            continue

                        result_data = result_response.json()["data"]
                        progress = result_data.get("progress", 0)
                        status = result_data.get("status", "unknown")
                        progress_bar.progress(progress / 100)
                        status_text.text(f"进度: {progress}% | 状态: {status} | 尝试: {attempt + 1}/{max_attempts}")

                        if result_data["status"] == "succeeded":
                            st.success("生成成功！")
                            img_url = result_data["results"][0]["url"]
                            st.image(img_url)

                            img_data = requests.get(img_url).content
                            st.download_button(
                                "下载图片",
                                img_data,
                                "schematic.png",
                                "image/png"
                            )
                            break
                        elif result_data["status"] == "failed":
                            st.error(f"生成失败: {result_data.get('error', result_data.get('failure_reason'))}")
                            st.json(result_data)  # 显示完整错误信息
                            break

                        time.sleep(2)
                        attempt += 1

                    if attempt >= max_attempts:
                        st.error("生成超时，请重试")
                        st.warning(f"最后状态: 进度 {progress}%, 状态 {status}")
                        st.info("提示：复杂图形可能需要更长时间，请稍后使用任务ID查询结果")
                else:
                    st.error(f"请求失败: {result.get('msg', '未知错误')}")

            except Exception as e:
                st.error(f"发生错误: {str(e)}")

# 示例提示词
with st.expander("💡 示例提示词"):
    st.markdown("""
    - 细胞膜上的受体结合配体，激活下游MAPK信号通路
    - 实验流程图：样本采集 → DNA提取 → PCR扩增 → 测序分析
    - 线粒体结构示意图，标注内外膜、嵴和基质
    - T细胞识别抗原呈递细胞，TCR与MHC-II结合
    - 免疫检查点抑制剂阻断PD-1/PD-L1相互作用
    """)

st.divider()
st.caption("提示：生成的图片链接有效期为2小时，请及时下载保存")
