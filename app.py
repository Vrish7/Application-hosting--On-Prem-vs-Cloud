import streamlit as st
import pandas as pd

# Load CSV
uploaded_file = st.file_uploader("Upload Application Classification CSV", type="csv")
if uploaded_file:
    classification_df = pd.read_csv(uploaded_file)

    # Define weights dictionary
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

    if app_name:
        row = classification_df[classification_df["Application Name"].str.lower().str.strip() == app_name.lower().strip()]

        if row.empty:
            st.warning("App not found. Please enter custom weights.")
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
                st.warning("App is unclassified. Please enter custom weights.")
                weights_input = st.text_input("Enter 7 weights separated by space")
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
