import streamlit as st
import pandas as pd
import plotly.express as px

# Load data from files
def load_data():
    file_paths = {
        "Distinction": "decoded_output_distinction_PrefixSpan (1).txt_50%",
        "Pass": "decoded_output_pass_PrefixSpan (1).txt_50%",
        "Fail": "decoded_output_fail_PrefixSpan (1).txt_50%",
        "Withdrawn": "decoded_output_withdrawn_PrefixSpan (1).txt_50%",
    }
    data = {}
    support_counts = {}
    for category, path in file_paths.items():
        sequences = []
        supports = []
        with open(path, 'r', encoding='utf-8') as file:
            for line in file:
                seq, sup = line.strip().split(' #SUP: ')
                sequences.append(seq)
                supports.append(int(sup))
        data[category] = sequences
        support_counts[category] = dict(zip(sequences, supports))
    return data, support_counts

# Extract unique activities from all sequences
def extract_unique_activities(data):
    unique_activities = set()
    for sequences in data.values():
        for seq in sequences:
            activities = [act for act in seq.split() if act != "-1"]
            unique_activities.update(activities)
    return sorted(unique_activities)

# Convert sequence string to readable format
def format_sequence(seq):
    days = seq.strip().split(" -1")
    return " -> ".join([" ".join(day.strip().split()) for day in days if day.strip()])

# Count number of days in a sequence
def count_days(seq):
    return seq.strip().split().count("-1")

# Create bar chart for support counts
def plot_support_counts(selected_sequence, support_counts):
    category_names = []
    sup_values = []

    for category, seq_counts in support_counts.items():
        if selected_sequence in seq_counts:
            category_names.append(category)
            sup_values.append(seq_counts[selected_sequence])

    if category_names:
        total_sup = sum(sup_values)
        percentages = [round((s / total_sup) * 100, 2) for s in sup_values]

        df = pd.DataFrame({
            'Category': category_names,
            'Support Count': sup_values,
            'Percentage': percentages
        })

        fig = px.bar(df, x='Category', y='Support Count',
                     text='Percentage', title='Support Count by Category',
                     labels={'Support Count': 'Number of Occurrences'})
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig)

        max_category = df.loc[df['Support Count'].idxmax(), 'Category']
        return f"The sequence is most associated with the {max_category} category.", max_category
    return "No support data available for this sequence.", None

# Suggest improvement based on better categories
def suggest_improvement(selected_sequence, support_counts):
    suggestions = []
    for category in ["Distinction", "Pass"]:
        seq_counts = support_counts.get(category, {})
        for seq, sup in seq_counts.items():
            if selected_sequence in seq and seq != selected_sequence:
                suggestions.append((seq, category, sup))
    if suggestions:
        suggestions.sort(key=lambda x: x[2], reverse=True)
        return suggestions[:3]
    return []

# Main Streamlit app
def main():
    st.title("Sequential Pattern Mining Demo")
    st.sidebar.header("Advanced Filters")

    data, support_counts = load_data()
    all_activities = extract_unique_activities(data)

    st.write("### Available Activities:")
    st.write(", ".join(all_activities))

    st.write("### Activity Descriptions:")
    activity_meanings = {
        "forumng": "Tham gia diễn đàn thảo luận",
        "homepage": "Truy cập vào trang chính của khóa học",
        "oucontent": "Xem nội dung học tập",
        "quiz": "Làm bài kiểm tra",
        "resource": "Truy cập tài nguyên học tập khác",
        "subpage": "Truy cập một mục phụ trên trang khóa học",
        "url": "Truy cập đường link ngoài hoặc trang web được nhúng",
    }
    df_meanings = pd.DataFrame(list(activity_meanings.items()), columns=["Activity", "Description"])
    st.table(df_meanings)

    if "day_count" not in st.session_state:
        st.session_state["day_count"] = 1

    day_count = st.sidebar.slider("Number of days", min_value=1, max_value=10, value=st.session_state["day_count"], key="day_count")

    selected_days = []
    for i in range(day_count):
        day_activities = st.sidebar.text_input(f"Activities for day {i+1} (separate by space)", key=f"day_{i+1}")
        selected_days.append(day_activities.strip())

    if st.sidebar.button("Confirm Sequence"):
        selected_sequence = " -1 ".join([d for d in selected_days if d]) + " -1"
        st.write(f"### Selected Sequence: {format_sequence(selected_sequence)}")

        category_decision, best_category = plot_support_counts(selected_sequence, support_counts)
        st.write(f"## Category Decision:")
        st.write(category_decision)

        suggestions = suggest_improvement(selected_sequence, support_counts)
        if suggestions:
            st.write("### Suggested Improvements:")
            for seq, category, sup in suggestions:
                st.write(f"- {format_sequence(seq)} (Category: {category}, Support: {sup})")
        else:
            st.write("### Suggested Improvements:")
            st.write("Current sequence does not have an improvement path towards Pass or Distinction. Consider exploring different activities.")

    # Top k sequences with minimum day length
    k = st.sidebar.slider("Top k sequences", min_value=1, max_value=20, value=5)
    min_days = st.sidebar.slider("Minimum number of days in sequence", min_value=1, max_value=10, value=1)

    for category, seq_counts in support_counts.items():
        filtered_seqs = [(seq, sup) for seq, sup in seq_counts.items() if count_days(seq) >= min_days]
        top_k = sorted(filtered_seqs, key=lambda x: x[1], reverse=True)[:k]
        if top_k:
            st.write(f"### Top {k} sequences in {category} with ≥ {min_days} days")
            df = pd.DataFrame(
                [(format_sequence(seq), sup) for seq, sup in top_k],
                columns=["Sequence", "Support Count"]
            )
            st.dataframe(df)

if __name__ == "__main__":
    main()
