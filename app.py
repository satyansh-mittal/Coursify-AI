import os
import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient
import google.generativeai as genai
from typing import List, Dict
import requests

# Load environment variables and configure APIs
load_dotenv()
tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

# Configure Streamlit page
st.set_page_config(
    page_title="Coursify",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton button {
        height: 42px;  /* Match input field height */
        margin-top: 24px;  /* Align with input field */
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
    }
    .stTextInput > div > div > input {
        border-radius: 5px;
    }
    .row-widget.stButton {
        padding: 0;
        margin: 0;
    }
    .stDownloadButton button {
        width: 100%;
        background-color: #2196F3;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        transition: all 0.3s ease;
        margin: 5px 0;
    }
    .stDownloadButton button:hover {
        background-color: #1976D2;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

def verify_api_keys() -> bool:
    """Verify that API keys are present and valid."""
    if not os.getenv('TAVILY_API_KEY') or not os.getenv('GOOGLE_API_KEY'):
        st.error("❌ Missing API keys. Please check your .env file.")
        return False
    return True

def search_sources(topic: str, max_results: int = 5) -> List[Dict]:
    """Search for relevant sources using Tavily API."""
    with st.spinner("🔎 Searching the web for relevant resources..."):
        try:
            tavily_search_results = tavily.search(
                query=topic,
                search_depth="advanced",
                max_results=max_results,
                search_type="comprehensive"
            )
            results = tavily_search_results.get('results', [])
            if not results:
                st.warning("⚠️ No search results found. The topic might be too specific.")
            return results
        except Exception as e:
            st.error(f"🚨 Search Error: {str(e)}")
            st.info("Please check your API keys and ensure they are valid.")
            return []

def hero_section():
    """Display the hero section of the app."""
    st.markdown("""
    <style>
    .hero {
        padding: 2rem;
        background: linear-gradient(135deg, #1e3d59 0%, #0a192f 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .hero h1 {
        color: #ffffff;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .hero p {
        color: #e0e0e0;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    </style>
    
    <div class="hero">
        <h1>🎓 AI Course Generator</h1>
        <p>Transform any topic into a comprehensive, engaging course outline with AI-powered insights!</p>
    </div>
    """, unsafe_allow_html=True)

def generate_course(topic: str, search_results: List[Dict]) -> str:
    """Generate a course outline using Gemini API."""
    description = "You are an experienced educator tasked with creating a comprehensive course outline on the given topic."
    instructions = [
        "Create an engaging and informative course outline based on the provided topic and search results.",
        "Structure the course like a detailed index with essential information for each section.",
        "Include an introduction, learning objectives, 4-5 main modules with 3-5 subtopics each, and a conclusion.",
        "For each concept or topic, provide a brief explanation followed by a relevant YouTube source link for further learning.",
        "Ensure the content is substantial, informative, and well-organized, resembling a comprehensive course page.",
        "Use markdown formatting to structure the document clearly and render formulas where applicable.",
        "If a programming language is entered, provide the same detailed information for it."
    ]

    # Template for course structure
    course_format = """
# {topic}

## Course Overview
[Provide a paragraph overview of the course, its importance, and what students will gain from it.]

## Learning Objectives
- Objective 1
- Objective 2
- Objective 3

## Course Outline

### Module 1: [Module Title]
[Module overview]

#### 1.1 [Subtopic]
- Concept explanation
- Key points
- Practice exercises
- Resources

[Continue with more modules...]

## Additional Resources
- Resource 1
- Resource 2
- Resource 3

## Assessment Methods
- Quiz suggestions
- Project ideas
- Practice exercises

## Conclusion
[Course summary and next steps]
    """

    prompt = f"{description}\n\nInstructions:\n" + "\n".join(f"- {instruction}" for instruction in instructions)
    prompt += f"\n\nTopic: {topic}\n\nSearch Results:\n"
    for result in search_results:
        prompt += f"- {result['title']}: {result['url']}\n"

    try:
        with st.spinner("🤖 AI is crafting your course outline..."):
            chat_completion = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            return chat_completion.text
    except Exception as e:
        st.error(f"🚨 Error generating course: {str(e)}")
        return None

def sidebar_info():
    """Display information in the sidebar."""
    with st.sidebar:
        st.markdown("### 📚 About")
        st.markdown("""
        This AI Course Generator helps create comprehensive course outlines for any topic.
        
        ### 🔑 Features:
        - 🎯 Detailed course structure
        - 📚 Learning objectives
        - 🔍 Web-sourced content
        - 📥 Downloadable outlines
        
        ### 💡 Tips:
        - Be specific with your topic
        - Try different variations
        - Download your results
        """)

def main():
    """Main application function."""
    if 'generated_course' not in st.session_state:
        st.session_state.generated_course = None
    if 'last_topic' not in st.session_state:
        st.session_state.last_topic = None

    if not verify_api_keys():
        return

    sidebar_info()
    hero_section()
    
    col1, col2 = st.columns([4, 1])
    with col1:
        input_topic = st.text_input(
            "Enter a course topic",
            placeholder="e.g., Python Programming, Machine Learning, Web Development",
            help="Enter any topic you'd like to learn about",
            key="topic_input"
        )
    with col2:
        st.write("")
        generate_course_btn = st.button("Generate Course 🚀")

    if generate_course_btn:
        if not input_topic.strip():
            st.warning("⚠️ Please enter a valid topic.")
            return
            
        if input_topic == st.session_state.last_topic and st.session_state.generated_course:
            st.markdown(st.session_state.generated_course)
        else:
            search_results = search_sources(input_topic)
            if search_results:
                final_course = generate_course(input_topic, search_results)
                if final_course:
                    st.session_state.generated_course = final_course
                    st.session_state.last_topic = input_topic
                    
                    st.markdown("### 📋 Generated Course Outline")
                    st.markdown(final_course)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download as Markdown",
                            data=final_course,
                            file_name=f"{input_topic.replace(' ', '_')}_course_outline.md",
                            mime="text/markdown",
                            key="download_md"
                        )
                    with col2:
                        st.download_button(
                            label="📥 Download as Text",
                            data=final_course,
                            file_name=f"{input_topic.replace(' ', '_')}_course_outline.txt",
                            mime="text/plain",
                            key="download_txt"
                        )
                    
                    st.markdown("### 📝 Feedback")
                    feedback = st.radio(
                        "Was this course outline helpful?",
                        options=["Very Helpful", "Somewhat Helpful", "Not Helpful"],
                        horizontal=True
                    )
                    if feedback:
                        st.success("Thanks for your feedback! 🙏")

if __name__ == "__main__":
    main()