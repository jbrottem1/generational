# 🚀 Generational

**The AI Content Operating System**

Generational is an AI-powered faceless content operating system designed to help creators generate, produce, and distribute content at scale.

## MVP Features

- Select a content category (Psychology, AI & Future Tech, History, Space, Finance, Health)
- Enter a topic
- Generate 10 placeholder content ideas
- Preview of upcoming features (Coming Soon section)

## Coming Soon

- AI Script Writer
- AI Voice Generation
- AI Video Creation
- SEO Optimizer
- Auto Posting
- Analytics Dashboard

## Getting Started

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root and add your OpenAI API key (used by future AI-powered features):

```
OPENAI_API_KEY=your_api_key_here
```

### 4. Run the app

```bash
streamlit run app.py
```

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [OpenAI](https://openai.com/) — AI content generation (future integration)
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management

## Project Structure

```
generational/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```
