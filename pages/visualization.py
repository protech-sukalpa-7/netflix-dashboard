import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

st.set_page_config(layout='wide')

st.title("Netflix Content Analysis Dashboard")
st.write("This dashboard provides insights into Netflix content, including data quality, content distribution, top contributors, and trends over time.")

@st.cache_data
def load_data():
    df = pd.read_csv('netflix_titles.csv')
    # Handle Missing Director Names
    df['director'].fillna('Unknown', inplace=True)
    # Handle Missing Country Names
    df['country'].fillna('Unknown', inplace=True)
    # Drop rows with null 'date_added' to ensure correct date processing for yearly trends
    df.dropna(subset=['date_added'], inplace=True)
    # Convert 'date_added' to datetime and extract 'year_added'
    df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
    df['year_added'] = df['date_added'].dt.year.astype('Int64') # Use Int64 for nullable integer

    # Prepare for duration numeric and correlation
    df_corr = df.copy()
    def convert_duration_to_numeric(row):
        if pd.isnull(row['duration']):
            return np.nan
        elif 'min' in row['duration']:
            return int(row['duration'].replace(' min', ''))
        elif 'Season' in row['duration']:
            return int(row['duration'].replace(' Seasons', '').replace(' Season', ''))
        return np.nan
    df_corr['duration_numeric'] = df_corr.apply(convert_duration_to_numeric, axis=1)
    return df, df_corr

df, df_corr = load_data()


st.sidebar.header("Dashboard Navigation")
selected_analysis = st.sidebar.radio(
    "Go to",
    [
        "Data Overview",
        "Content Type Distribution",
        "Top Entities by Title Count",
        "Titles Added by Release Year Range",
        "Rating Distribution by Content Type",
        "Genre Trend by Release Year",
        "Duration and Correlation Analysis"
    ]
)


if selected_analysis == "Data Overview":
    st.header("1. Data Overview")
    st.markdown("### Here's a quick look at the dataset's health and composition.")
    st.write("### Missing Values and Duplicates")
    st.markdown("This section shows how much data is missing in each column and if there are any duplicate entries. It's crucial for understanding data quality.")
    st.code(f"Missing values per column:\n{df.isnull().sum()}\n\nTotal duplicate rows: {df.duplicated().sum()}")

    st.write("### Content Type Counts")
    st.markdown("This tells us whether Netflix has more Movies or TV Shows. It gives a basic idea of their content strategy.")
    content_type_counts = df['type'].value_counts()
    st.code(f"Content Type Distribution:\n{content_type_counts}")

    st.write("### Top 10 Countries by Title Count")
    st.markdown("Here, we see which countries produce the most content on Netflix. This helps identify key content markets.")
    countries = df['country'].str.split(', ').explode()
    top_10_countries = countries.value_counts().head(10)
    st.code(f"Top 10 Countries by Title Count:\n{top_10_countries}")

elif selected_analysis == "Content Type Distribution":
    st.header("2. Content Type Distribution (Movie/TV Show Selector)")
    st.markdown("This chart helps us see the breakdown of movies versus TV shows. You can pick 'Movie', 'TV Show', or 'All' to filter the view. \n\n**Insight:** A higher number of movies suggests that Netflix might be focusing more on film content, or perhaps movie releases are simply more frequent than TV show seasons.")
    content_selection = st.radio("Enter content type to visualize:", ('All', 'Movie', 'TV Show'))

    fig, ax = plt.subplots(figsize=(8, 5))
    if content_selection.lower() == 'movie':
        sns.countplot(data=df[df['type'] == 'Movie'], x='type', palette='deep', ax=ax)
        ax.set_title('Distribution of Movies')
    elif content_selection.lower() == 'tv show':
        sns.countplot(data=df[df['type'] == 'TV Show'], x='type', palette='deep', ax=ax)
        ax.set_title('Distribution of TV Shows')
    elif content_selection.lower() == 'all':
        sns.countplot(data=df, x='type', palette='deep', ax=ax)
        ax.set_title('Distribution of All Content Types')

    ax.set_xlabel('Content Type')
    ax.set_ylabel('Number of Titles')
    plt.tight_layout()
    st.pyplot(fig)

elif selected_analysis == "Top Entities by Title Count":
    st.header("3. Top N Directors/Countries/Genres by Title Count")
    st.markdown("This section identifies the biggest contributors to Netflix content...")
    
    num_top_entities = st.slider("Enter the number of top entities to display:", 1, 20, 10)
    column_to_analyze = st.selectbox("Enter the column to analyze:", ('director', 'country', 'listed_in'))

    # Logic to prepare data remains exactly as you defined it
    if column_to_analyze == 'country':
        entities = df['country'].str.split(', ').explode()
    elif column_to_analyze == 'listed_in':
        entities = df['listed_in'].str.split(', ').explode()
    elif column_to_analyze == 'director':
        entities = df['director']
        entities = entities[entities != 'Unknown'] 
    else:
        entities = df[column_to_analyze]

    top_entities = entities.value_counts().head(num_top_entities)

    # --- HORIZONTAL BARPLOT CHANGES BELOW ---
    fig, ax = plt.subplots(figsize=(12, 8)) # Increased height slightly for better readability

    # We swap: x becomes the values (counts), y becomes the index (names)
    sns.barplot(x=top_entities.values, y=top_entities.index, palette='plasma', ax=ax)
    
    ax.set_title(f'Top {num_top_entities} {column_to_analyze.replace("_", " ").title()} by Title Count')
    ax.set_xlabel('Number of Titles') # Swapped Label
    ax.set_ylabel(column_to_analyze.replace("_", " ").title()) # Swapped Label
    
    # We remove plt.xticks(rotation=60) because horizontal labels are easier to read
    plt.tight_layout()
    st.pyplot(fig)

elif selected_analysis == "Titles Added by Release Year Range":
    st.header("4. Titles Added by Release Year Range")
    st.markdown("This graph shows how many titles were added to Netflix each year within a selected period. It helps us understand the growth of content over time.\n\n**Insight:** A rising trend suggests that Netflix is aggressively expanding its content library, which could be a response to subscriber growth or increased competition.")
    min_year = int(df['release_year'].min())
    max_year = int(df['release_year'].max())
    start_year, end_year = st.slider("Select release year range:", min_year, max_year, (2010, 2020))

    filtered_years = df[(df['release_year'] >= start_year) & (df['release_year'] <= end_year)]
    year_counts_filtered = filtered_years['release_year'].value_counts().sort_index()

    if not year_counts_filtered.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(x=year_counts_filtered.index, y=year_counts_filtered.values, marker='o', color='green', ax=ax)
        ax.set_title(f'Number of Titles Released Between {start_year} and {end_year}')
        ax.set_xlabel('Release Year')
        ax.set_ylabel('Number of Titles')
        plt.xticks(rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.write(f"No data available for the release year range {start_year}-{end_year}.")

elif selected_analysis == "Rating Distribution by Content Type":
    st.header("5. Rating Distribution for a Specific Content Type")
    st.markdown("This chart displays the different age ratings (like PG, TV-MA) for either Movies or TV Shows. It tells us what kind of audience Netflix targets for each content type.\n\n**Insight:** Understanding the rating distribution can show if Netflix favors content for general audiences, or if it has a stronger focus on mature content, helping to understand its target demographic.")
    content_type_filter = st.radio("Filter ratings for:", ('Movie', 'TV Show'))

    filtered_df = df[df['type'].str.lower() == content_type_filter.lower()]
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.countplot(data=filtered_df, x='rating', palette='cividis', order=filtered_df['rating'].value_counts().index, ax=ax)
        ax.set_title(f'Distribution of Content Ratings for {content_type_filter.title()}s')
        ax.set_xlabel('Rating')
        ax.set_ylabel('Number of Titles')
        plt.xticks(rotation=45)
        ax.grid(axis='y', linestyle='--')
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.write(f"No {content_type_filter.title()}s found with rating data.")

elif selected_analysis == "Genre Trend by Release Year":
    st.header("6. Content Categories (Genres) by Release Year Trend")
    st.markdown("This line graph shows how a specific genre has grown (or shrunk) on Netflix over the years. You can pick any genre to see its popularity trend.\n\n**Insight:** Observing genre trends can reveal shifting audience preferences or Netflix's strategic moves, like investing more in certain genres (e.g., K-dramas) based on global popularity.")
    all_genres = df['listed_in'].str.split(', ').explode().unique()
    selected_genre = st.selectbox("Select a specific genre to analyze:", all_genres)

    genre_df = df[df['listed_in'].str.contains(selected_genre, case=False, na=False)].copy()

    if not genre_df.empty:
        genre_df['release_year'] = pd.to_numeric(genre_df['release_year'], errors='coerce')
        genre_yearly_counts = genre_df['release_year'].value_counts().sort_index()
        genre_yearly_counts = genre_yearly_counts.dropna()

        if not genre_yearly_counts.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.lineplot(x=genre_yearly_counts.index, y=genre_yearly_counts.values, marker='o', color='purple', ax=ax)
            ax.set_title(f'Trend of \'{selected_genre.title()}\' Titles by Release Year')
            ax.set_xlabel('Release Year')
            ax.set_ylabel('Number of Titles')
            plt.xticks(rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.write(f"No release year data available for the genre '{selected_genre}'.")
    else:
        st.write(f"No titles found for the genre '{selected_genre}'. Please check the spelling or try another genre.")

elif selected_analysis == "Duration and Correlation Analysis":
    st.header("7. Duration and Correlation Analysis")
    st.markdown("This section looks at how long content typically is (movies in minutes, TV shows in seasons) and how this relates to their release year. This helps us understand if content length has changed over time.\n\n**Insight:** A negative correlation between release year and duration for movies could mean that newer movies tend to be shorter, potentially due to changing consumption habits. For TV shows, a similar trend could suggest a move towards shorter series or more miniseries.")

    st.subheader("Distribution of Numerical Duration")
    st.markdown("This histogram shows how often different durations appear in the dataset. It helps us see the typical length of content on Netflix.")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.histplot(df_corr['duration_numeric'], bins=50, kde=True, color='purple', ax=ax)
    ax.set_title('Distribution of Numerical Duration (Minutes/Seasons)')
    ax.set_xlabel('Duration (Minutes for Movies, Seasons for TV Shows)')
    ax.set_ylabel('Number of Titles')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("Correlation Map: Release Year and Duration")
    st.markdown("This heatmap visualizes the relationship between the release year and the content's duration. A correlation close to 1 means they move together, close to -1 means they move opposite, and close to 0 means no clear relationship.")
    correlation_data = df_corr[['release_year', 'duration_numeric']].dropna()
    correlation_matrix = correlation_data.corr()

    st.write("Correlation Matrix:")
    st.write(correlation_matrix)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5, ax=ax)
    ax.set_title('Correlation Matrix of Release Year and Numerical Duration')
    st.pyplot(fig)


