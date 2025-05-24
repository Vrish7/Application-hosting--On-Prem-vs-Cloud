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
    app_desc = st.text_area("Enter a short description of the app (for AI classification if unrecognized)")

    if app_name:
        row = classification_df[classification_df["Application Name"].str.lower().str.strip() == app_name.lower().strip()]

        if not row.empty:
            classification = row.iloc[0]["App Classification"].strip().lower()
            if "+" in classification or "," in classification:
                delimit = "+" if "+" in classification else ","
                cat1, cat2 = map(str.strip, classification.split(delimit))
                st.info(f"Multi-category: {cat1.title()} + {cat2.title()}")
                split_input = st.text_input("Enter split ratio (e.g. 60 40)")
                if split_input:
                    try:
                        r1, r2 = map(int, split_input.split())
                        if r1 + r2 != 100:
                            raise ValueError
                        w1 = category_weights[cat1]
                        w2 = category_weights[cat2]
                        weights = [(r1/100)*w1[i] + (r2/100)*w2[i] for i in range(7)]
                        result = calculate_scores(weights)
                        st.success("Scores calculated.")
                        st.json(result)
                    except:
                        st.error("Invalid input or ratio.")
            elif classification in category_weights:
                weights = category_weights[classification]
                result = calculate_scores(weights)
                st.success(f"Scores calculated for {classification.title()}.")
                st.json(result)
            else:
                st.warning("Unclassified app in Excel. Please enter 7 weights manually.")
                weights_input = st.text_input("Enter 7 weights separated by space:")
                if weights_input:
                    try:
                        weights = list(map(float, weights_input.split()))
                        if len(weights) != 7:
                            raise ValueError
                        result = calculate_scores(weights)
                        st.success("Scores calculated.")
                        st.json(result)
                    except:
                        st.error("Enter exactly 7 numeric values.")

        elif gpt_enabled and app_desc:
            st.warning("App not found. Asking GPT for a suggested classification...")
            with st.spinner("Classifying via AI..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You're an expert in classifying enterprise IT applications."},
                        {"role": "user", "content": f"Classify this app into one of the following: Transactional App, Analytics App, Compliance-Centric App, Scalable Web App, ERP App, Compliance Sensitive App.\n\nApp name: {app_name}\nDescription: {app_desc}"}
                    ]
                )
                classification = response.choices[0].message.content.strip().lower()
                st.info(f"AI Suggested Classification: {classification}")

                classification_type = st.radio("Select classification type", ["Single Category", "Multi Category"])

                if classification_type == "Single Category":
                    selected_cat = st.selectbox("Select category", list(category_weights.keys()))
                    if selected_cat:
                        weights = category_weights[selected_cat]
                        result = calculate_scores(weights)
                        st.success(f"Scores for {selected_cat.title()}:")
                        st.json(result)

                elif classification_type == "Multi Category":
                    cat1 = st.selectbox("Select first category", list(category_weights.keys()), key="cat1")
                    cat2 = st.selectbox("Select second category", list(category_weights.keys()), key="cat2")
                    split = st.text_input("Enter split ratio (e.g., 60 40)")
                    if split:
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
                            st.error("Invalid input. Enter two numbers adding to 100.")
