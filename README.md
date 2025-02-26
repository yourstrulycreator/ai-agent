# LinkedIn AI Agent

An AI-powered agent for automated LinkedIn data collection and analysis.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-agent.git
cd ai-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv ai-agent_env
source ai-agent_env/bin/activate  # On Windows: ai-agent_env\Scripts\activate
 ```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
```bash
cp config.template.py config.py
```

Then edit config.py with your LinkedIn credentials and preferences.

## Security Note
- Never commit your config.py file as it contains sensitive information
- The repository includes config.template.py as a template
- Your actual config.py is ignored by git for security

## Usage
Run the main script:
```bash
python main.py
```

## Testing
Run the test suite:
```bash
python test.py
```

## Features
- Automated LinkedIn profile data extraction
- AI-powered navigation and decision making
- Human-like behavior simulation
- Rate limiting and anti-detection measures
- Data export in CSV and JSON formats