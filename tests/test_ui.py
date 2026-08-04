import re

def test_c_level_full_flow(page):
    page.goto("http://localhost:8501", timeout=60000)
    page.get_by_role("textbox", name="Username").fill("admin")
    page.get_by_role("textbox", name="Password").fill("admin123")
    page.get_by_role("button", name="Login").click()
    page.wait_for_selector("text=You have global access", timeout=10000)

    page.get_by_role("tab", name="👤 Admin (C-Level)").click()
    page.get_by_role("heading", name="Create New Role")
    
    page.get_by_text("New Role Name")
    page.get_by_role("textbox", name="New Role Name").fill("QA Team")
    page.get_by_role("button", name="Add Role").click()
    page.wait_for_selector("text=Role 'QA Team' created", timeout=15000)

    page.wait_for_timeout(15000)
    
    page.get_by_role("heading", name="Add User").wait_for(timeout=15000)
    page.get_by_text("New Username")
    page.get_by_role("textbox", name="New Username").fill("qa_user")
    page.get_by_text("New Password")
    page.get_by_role("textbox", name="New Password").fill("qa_pass")
    page.get_by_text("Assign Role")

    dropdown = page.get_by_role("combobox")
    dropdown.wait_for(timeout=15000)
    dropdown.click()

    dropdown_popup = page.get_by_test_id("stSelectboxVirtualDropdown")
    dropdown_popup.get_by_text("QA Team", exact=True).click()

    page.get_by_role("button", name="Create User").click()
    page.wait_for_selector("text=User 'qa_user' added", timeout=15000)
    
    page.get_by_role("tab", name="🧾 Upload (C-Level)").click()
    page.get_by_text("Select document access role")

    dropdown = page.get_by_role("combobox")
    dropdown.wait_for(timeout=15000)
    dropdown.click()

    dropdown_popup = page.get_by_test_id("stSelectboxVirtualDropdown")
    dropdown_popup.get_by_text("C-Level", exact=True).click()
    dropdown.wait_for(timeout=15000)

    page.get_by_text("Upload document (.md or .csv)")

    page.get_by_test_id("stFileUploaderDropzone").wait_for(timeout=5000)

    page.locator('input[type="file"]').set_input_files("tests/sample_docs/sample_hr.md")

    dropdown.wait_for(timeout=15000)
    
    
    
    page.get_by_role("button", name="Upload Document").click()
    page.wait_for_timeout(15000)
    page.wait_for_selector("text=sample_hr.md uploaded successfully for role 'c-level'", timeout=15000)

    page.get_by_role("button", name="Logout").click()
    page.wait_for_selector("text=Login", timeout=15000)
    
    page.get_by_role("textbox", name="Username").fill("qa_user")
    page.get_by_role("textbox", name="Password").fill("qa_pass")
    page.get_by_role("button", name="Login").click()

    page.wait_for_selector("text=You have access to documents and features related", timeout=15000)
    page.wait_for_selector("text=You also have access to General documents (e.g., company policies, holidays, announcements)")
    
    assert page.locator('text=👤 Admin (C-Level)').count() == 0
    assert page.locator('text=🧾 Upload (C-Level)').count() == 0

    page.get_by_role("heading", name="Ask a question")
    page.get_by_text("Your question")
    page.get_by_role("textbox",name="Your question").fill("Tell me something")
    page.get_by_role("button", name="Submit").click()

    page.wait_for_selector("text=Answer:", timeout=10000)

    page.get_by_role("button", name="Logout").click()
    page.wait_for_selector("text=Login", timeout=15000)
    
    page.get_by_role("textbox", name="Username").fill("Tony")
    page.get_by_role("textbox", name="Password").fill("wrongpassword")
    page.get_by_role("button", name="Login").click()

    page.wait_for_selector("text=Invalid credentials", timeout=5000)
    
