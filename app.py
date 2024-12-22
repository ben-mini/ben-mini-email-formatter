import streamlit as st
import requests
from markdown2 import markdown
from bs4 import BeautifulSoup
from datetime import datetime

# App Title
st.set_page_config(page_title="ben-mini Email Formatter", layout="centered")
st.title("ben-mini Email Formatter")

# Sidebar Configuration
st.sidebar.header("Available Articles")

# Global Variables
secondary_color = "#4bae34"
font_family = "'Arial', sans-serif"  # Closest approximation to Noto Sans for email
blog_logo_url = "https://ben-mini.com/assets/images/ben-mini-full.png"

# GitHub API Configuration
GITHUB_REPO = "ben-mini/ben-mini.github.io"
BRANCH = "gh-pages"
POSTS_PATH = "_posts"

# GitHub API to fetch files
@st.cache_data
def fetch_markdown_files():
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{POSTS_PATH}?ref={BRANCH}"
    response = requests.get(api_url)
    if response.status_code == 200:
        files = response.json()
        markdown_files = [file['name'] for file in files if file['name'].endswith(".md")]
        return list(reversed(markdown_files))  # Reverse the list order
    else:
        st.error("Failed to fetch markdown files from GitHub.")
        return []

# GitHub API to fetch file content
def fetch_file_content(filename):
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{POSTS_PATH}/{filename}"
    response = requests.get(raw_url)
    if response.status_code == 200:
        return response.text
    else:
        st.error(f"Failed to fetch content for {filename}.")
        return ""

# Fetch files and display in the sidebar
markdown_files = fetch_markdown_files()
selected_file = st.sidebar.selectbox("Select a file", markdown_files)

if selected_file:
    markdown_input = fetch_file_content(selected_file)
    st.sidebar.success(f"Loaded: {selected_file}")
else:
    markdown_input = ""

# Markdown Input Area
st.header("Edit or Preview Markdown")
markdown_input = st.text_area("Markdown Content", markdown_input, height=400)

# HTML Rendering Button
if st.button("Generate Email"):
    if markdown_input:
        # Parse Front Matter
        lines = markdown_input.splitlines()
        metadata_lines, content_lines = [], []
        in_metadata = False
        yaml_count = 0

        for line in lines:
            if line.startswith("---"):
                yaml_count += 1
                if yaml_count <= 2:  # Ignore the first two '---' (YAML front matter)
                    in_metadata = not in_metadata
                    continue
            if in_metadata:
                metadata_lines.append(line)
            else:
                content_lines.append(line)

        # Extract Metadata
        metadata = {}
        for line in metadata_lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                metadata[key.strip()] = value.strip().strip('"')

        title = metadata.get("title", "Untitled")
        raw_date = metadata.get("date", "Unknown Date")
        date = (
            datetime.strptime(raw_date, "%Y-%m-%d").strftime("%B %d, %Y")
            if raw_date != "Unknown Date"
            else "Unknown Date"
        )
        og_image = metadata.get("header", {}).get("og_image", "").replace("../assets/images/", "https://ben-mini.com/assets/images/")

        # Generate Article URL
        year = raw_date.split("-")[0] if raw_date != "Unknown Date" else "unknown"
        default_slug = title.lower().replace(" ", "-")
        article_url = f"https://ben-mini.com/{year}/{default_slug}"
        article_url = st.sidebar.text_input("Article URL", value=article_url)

        # Convert Markdown to HTML
        raw_html = markdown("\n".join(content_lines))

        # Clean and Validate HTML with BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")
        for img in soup.find_all("img"):
            img['src'] = img['src'].replace("../assets/images/", "https://ben-mini.com/assets/images/")
            img[
                'style'] = "display: block; margin: 0 auto; max-width: 100%; height: auto;"  # Resize images to fit within the container
        for hr in soup.find_all("hr"):
            hr['style'] = f"border: 1px solid {secondary_color};"
        for blockquote in soup.find_all("blockquote"):
            blockquote[
                'style'] = f"border-left: 4px solid {secondary_color}; padding-left: 10px; font-style: italic; color: #555;"
        for a in soup.find_all("a"):
            a['style'] = f"color: {secondary_color}; text-decoration: underline;"

        # Combine Main Content with Unsubscribe Footer
        content_html = str(soup)

        # Compose HTML Email
        email_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: {font_family};
                    margin: 0;
                    padding: 0;
                    background-color: #e8f6e4; /* Outer background color */
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #e8f6e4;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #e8f6e4; margin: 0; padding: 0;">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <!-- Container Table -->
                        <table width="700" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                            <tr>
                                <td style="text-align: left; font-family: {font_family};">
                                    <!-- View in Browser -->
                                    <p style="margin: 0 0 10px; font-size: 14px;">
                                        <a href="{article_url}" style="color: {secondary_color}; text-decoration: underline;">View in Browser</a>
                                    </p>
                                    <!-- Header -->
                                    <div style="text-align: center; margin-bottom: 20px;">
                                        <img src="{blog_logo_url}" alt="ben-mini logo" style="max-width: 100%; height: auto;">
                                    </div>
                                    <!-- Title -->
                                    <h1 style="font-size: 24px; color: #333; margin: 0 0 10px;">{title}</h1>
                                    <!-- Date -->
                                    <p style="font-size: 14px; color: #666; margin: 0 0 20px;">{date}</p>
                                    <!-- Divider -->
                                    <hr style="border: 1px solid {secondary_color}; margin: 20px 0;">
                                    <!-- Content -->
                                    <div style="font-size: 16px; color: #333; line-height: 1.6;">
                                        {content_html}
                                    </div>
                                    <!-- Unsubscribe -->
                                    <hr style="border: 1px solid {secondary_color}; margin: 20px 0;">
                                    <p style="font-size: 12px; color: #666; text-align: center; margin: 0;">
                                        <a href="https://tally.so/r/w4PVQr" style="color: {secondary_color}; text-decoration: underline;">Unsubscribe</a>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        # Display Output
        st.markdown(email_html, unsafe_allow_html=True)

        # Copyable HTML Area
        st.text_area("Copy HTML Output", email_html, height=400)

        # Add a download button
        st.download_button("Download HTML Email", email_html, file_name="newsletter.html", mime="text/html")

    else:
        st.error("Please paste your Markdown content.")
