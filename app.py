import streamlit as st
import pandas as pd

try:
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets["openai_api_key"])
    gpt_enabled = True
except Exception as e:
    st.warning("OpenAI API key not found or incorrect. AI classification disabled.")
    gpt_enabled = False

uploaded_file = st.file_uploader("Upload Application Classification CSV", type="csv")
if uploaded_file:
    classification_df = pd.read_csv(uploaded_file)

    category_weights = {
        "transactional app":           [0.25, 0.2, 0.15, 0.1, 0.1, 0.1, 0.1],
        "analytics app":               [0.1, 0.1, 0.2, 0.2, 0.1, 0.2, 0.1],
        "compliance-centric app":     [0.1, 0.1, 0.3, 0.2, 0.15, 0.1, 0.2],
        "scalable web app":           [0.15, 0.15, 0.1, 0.1, 0.1, 0.3, 0.1],
        "erp app":                    [0.2, 0.15, 0.25, 0.15, 0.1, 0.05, 0.1],
        "compliance sensitive app":   [0.1, 0.1, 0.35, 0.1, 0.1, 0.05, 0.2]
    }

    cloud_scores = {
        "Cloud-Native":    [9, 6, 7, 8, 9, 10, 9],
        "Cloud-VMware":    [8, 7, 8, 9, 8, 8, 8],
        "On-Prem":         [8, 9, 9, 9, 7, 6, 7]
    }

    def calculate_scores(weights):
        return {
            "Cloud-Native Score":  round(sum(w * s for w, s in zip(weights, cloud_scores["Cloud-Native"])), 2),
            "Cloud-VMware Score":  round(sum(w * s for w, s in zip(weights, cloud_scores["Cloud-VMware"])), 2),
            "On-Prem Score":       round(sum(w * s for w, s in zip(weights, cloud_scores["On-Prem"])), 2)
        }

    app_name = st.text_input("Enter Application Name")
    app_desc = st.text_area("Enter a short description of the app (for AI suggestion)")

    if app_name:
        row = classification_df[classification_df["Application Name"].str.lower().str.strip() == app_name.lower().strip()]

        if row.empty and gpt_enabled and app_desc:
            st.warning("App not found. Asking GPT for a suggestion...")
            with st.spinner("Consulting AI..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You're an expert in classifying enterprise IT applications."},
                        {"role": "user", "content": f"Suggest the best category for this app from the following: Transactional App, Analytics App, Compliance-Centric App, Scalable Web App, ERP App, Compliance Sensitive App.\n\nApp name: {app_name}\nDescription: {app_desc}"}
                    ]
                )
                gpt_suggestion = response.choices[0].message.content.strip()
                st.info(f"🤖 GPT Suggestion: {gpt_suggestion}")

                classification_mode = st.radio("Choose classification type:", ["Single Category", "Multi Category"])

                if classification_mode == "Single Category":
                    category = st.selectbox("Select category", list(category_weights.keys()))
                    if category and st.button("Calculate Scores"):
                        weights = category_weights[category]
                        result = calculate_scores(weights)
                        st.success(f"Scores for {category.title()} app:")
                        st.json(result)

                elif classification_mode == "Multi Category":
                    cat1 = st.selectbox("Select first category", list(category_weights.keys()), key="multi1")
                    cat2 = st.selectbox("Select second category", list(category_weights.keys()), key="multi2")
                    split = st.text_input("Enter split ratio (e.g., 60 40)")
                    if split and st.button("Calculate Scores for Multi Category"):
                        try:
                            r1, r2 = map(int, split.split())
                            if r1 + r2 != 100:
                                raise ValueError
                            w1 = category_weights[cat1]
                            w2 = category_weights[cat2]
                            weights = [(r1/100)*w1[i] + (r2/100)*w2[i] for i in range(7)]
                            result = calculate_scores(weights)
                            st.success(f"Scores for {cat1.title()} + {cat2.title()} ({r1}:{r2} split):")
                            st.json(result)
                        except:
                            st.error("Invalid split. Enter two numbers adding to 100.")
