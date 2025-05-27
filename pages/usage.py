import streamlit as st

st.set_page_config(
    page_title="OpenCourses",
    layout="wide"
)

usage_content = """
# How to Use OpenCourses

Welcome to OpenCourses! This guide will walk you through how to make the most of our platform, whether you're a teacher creating content or a student accessing course materials.

### Creating Your First Course
   - Click "New Course" from your dashboard
   - Fill in the basics:
     - Course name (e.g., "Introduction to Astronomy")
     - Course code
     - Grade level
     - Course description (optional)

   ![Create Course Interface](placeholder_create_course.png)

### Building Your Course

#### 📝 Content Creation
- **Organize Your Material**
  - Break your course into logical units
  - Add sections within each unit
  - Easily reorganize content as needed

- **Create Content with AI Help**
  - Use our AI teaching assistant to:
    - Generate course materials faster
    - Get suggestions for improvements
    - Format documents professionally
  
  ![AI Assistant Interface](placeholder_ai_assistant.png)

#### 🤖 Custom AI Tutors
- **Set Up Student Assistants**
  - Create specialized AI helpers for different course sections
  - Customize each AI to be an expert in specific topics

- **Managing Your AI Tutors**
  - Assign different helpers to specific sections
  - Fine-tune the instructions to match your teaching style

### 📤 Sharing and Collaboration
- Make your course "Open to All" to share with the community
- Share your course URL directly with students
- Export materials in various formats (Word, PDF, text)

## 💡 Pro Tips

- Use templates to speed up course creation
- Create different AI tutors for different learning styles
- Regular updates keep content fresh and engaging

---

"""

st.markdown(usage_content, unsafe_allow_html=True)