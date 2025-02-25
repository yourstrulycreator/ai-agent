from ai_controller import AIController
import time

def test_ai_controller():
    print("Testing AI controller...")
    
    # Initialize AI controller
    ai = AIController()
    
    # Test with sample page content
    sample_content = """
    <div class="profile-container">
        <img class="profile-picture" src="profile.jpg" alt="Profile Picture">
        <h1 class="text-heading-xlarge">John Doe</h1>
        <div class="text-body-medium">Software Engineer at Example Corp</div>
        <span class="text-body-small">Example Corp</span>
        <span class="text-body-small">San Francisco, California</span>
        <section class="experience">
            <h3>Experience</h3>
            <div>Software Engineer</div>
            <div>Example Corp</div>
            <div>2020 - Present</div>
        </section>
    </div>
    """
    
    # Test decision making
    print("Testing decision making...")
    action = ai.decide_next_action(sample_content, "Viewing profile")
    print(f"Decided action: {action}")
    
    # Test element identification
    print("Testing element identification...")
    for data_type in ["name", "job_title", "company", "location"]:
        selector = ai.identify_elements(sample_content, data_type)
        print(f"Selector for {data_type}: {selector}")
        
        # Also test fallback selectors
        fallback = ai.fallback_selectors(data_type)
        print(f"Fallback selector for {data_type}: {fallback}")
    
    print("AI controller test completed")

if __name__ == "__main__":
    test_ai_controller()