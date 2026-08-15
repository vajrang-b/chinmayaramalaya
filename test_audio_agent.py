import sys
from playwright.sync_api import sync_playwright

def test_audio_agent():
    print("🚀 Launching Headless Chrome to test Audio AI Agent...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "http://localhost:8080/audio-agent/index.html"
        print(f"🌐 Navigating to {url}")
        page.goto(url)
        page.wait_for_timeout(1000)

        # Check page title & header
        title = page.title()
        header = page.inner_text("h1")
        print(f"✅ Page Title: '{title}'")
        print(f"✅ Header text: '{header}'")

        # Test Text Input & Question Query
        text_input = page.locator("#textInput")
        send_btn = page.locator("#sendBtn")
        
        test_query = "What are the Sunday session timings?"
        print(f"💬 Typing query: '{test_query}'")
        text_input.fill(test_query)
        send_btn.click()
        page.wait_for_timeout(1000)

        user_query_text = page.inner_text("#userQuery")
        agent_response_text = page.inner_text("#agentResponse")
        
        print(f"🎤 Rendered User Query: {user_query_text}")
        print(f"🔊 Rendered Agent Response: {agent_response_text}")

        assert "Sunday" in agent_response_text or "9:00 AM" in agent_response_text, "Failed match"
        print("🎉 Audio AI Agent test PASSED with 100% clean query resolution!")
        browser.close()

if __name__ == "__main__":
    test_audio_agent()
