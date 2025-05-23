import streamlit as st
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai_api_key"])

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

        if row.empty:
            st.warning("App not found. Asking GPT for a suggested classification.")
            if app_desc:
                with st.spinner("Asking AI to classify the app..."):
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You're an expert in classifying enterprise IT applications."},
                            {"role": "user", "content": f"Classify this app into one of the following: Transactional App, Analytics App, Compliance-Centric App, Scalable Web App, ERP App, Compliance Sensitive App.\n\nApp name: {app_name}\nDescription: {app_desc}"}
                        ]
                    )
                    classification_raw = response.choices[0].message.content.strip().lower()
                    matched_cat = None
                    for cat in category_weights:
                        if cat in classification_raw:
                            matched_cat = cat
                            break
                    st.info(f"AI Suggested Classification: {classification.title()}")

                    if any(cat in classification for cat in category_weights):
                        matched_cat = next(cat for cat in category_weights if cat in classification)
                        weights = category_weights[matched_cat]
                        result = calculate_scores(weights)
                        st.success(f"Scores calculated using AI-suggested classification: {matched_cat.title()}!")
                        st.json(result)
                    else:
                        st.warning("AI suggestion not in known categories. Please enter weights manually.")
                        weights_input = st.text_input("Enter 7 weights separated by space (order: Business Criticality, Performance & Latency, Compliance & Security, Integration Needs, Cost Consideration, Scalability & Elasticity, Team Capability & Readiness)")
                        if weights_input:
                            try:
                                weights = list(map(float, weights_input.split()))
                                if len(weights) != 7:
                                    raise ValueError
                                result = calculate_scores(weights)
                                st.success("Scores calculated successfully!")
                                st.json(result)
                            except:
                                st.error("Invalid input. Enter exactly 7 numeric weights.")
        else:
            classification = row.iloc[0]["App Classification"].strip().lower()
            if classification == "unclassified":
                st.warning("App is unclassified. Asking GPT for classification.")
                if app_desc:
                    with st.spinner("Asking AI to classify the app..."):
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You're an expert in classifying enterprise IT applications."},
                                {"role": "user", "content": f"Classify this app into one of the following: Transactional App, Analytics App, Compliance-Centric App, Scalable Web App, ERP App, Compliance Sensitive App.\n\nApp name: {app_name}\nDescription: {app_desc}"}
                            ]
                        )
                        classification = response.choices[0].message.content.strip().lower()
                        st.info(f"AI Suggested Classification: {classification.title()}")

                        if matched_cat:
    weights = category_weights[matched_cat]
                            result = calculate_scores(weights)
                            st.success(f"Scores calculated using AI-suggested classification: {matched_cat.title()}!")
                            st.json(result)
                        else:
                            st.warning("AI suggestion not in known categories. Please enter weights manually.")
                            weights_input = st.text_input("Enter 7 weights separated by space (order: Business Criticality, Performance & Latency, Compliance & Security, Integration Needs, Cost Consideration, Scalability & Elasticity, Team Capability & Readiness)")
                            if weights_input:
                                try:
                                    weights = list(map(float, weights_input.split()))
                                    if len(weights) != 7:
                                        raise ValueError
                                    result = calculate_scores(weights)
                                    st.success("Scores calculated successfully!")
                                    st.json(result)
                                except:
                                    st.error("Invalid input. Enter exactly 7 numeric weights.")
            elif "+" in classification or "," in classification:
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
                        weights = [(r1/100)*w1[i] + (r2/100)*w2[i] for i in range(len(w1))]
                        result = calculate_scores(weights)
                        st.success("Scores calculated successfully!")
                        st.json(result)
                    except:
                        st.error("Invalid input or category not found.")
            else:
                st.success(f"Single-category app: {classification.title()}")
                weights = category_weights.get(classification)
                if not weights:
                    st.error("Category not found in dictionary.")
                else:
                    result = calculate_scores(weights)
                    st.json(result)
