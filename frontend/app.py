import streamlit as st
import requests
import os
from datetime import datetime

# Backend URL from environment variable or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="Nordic Secure License Manager", page_icon="🔐")

def check_license():
    """Check license status with backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/license/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"valid": False, "message": "Could not verify license"}
    except requests.exceptions.RequestException:
        return {"valid": False, "message": "Backend connection failed"}

def activate_license(license_key: str):
    """Activate a license key"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/license/activate",
            json={"license_key": license_key},
            timeout=5
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}

def main():
    st.title("🔐 Nordic Secure License Manager")
    
    # Check license status
    license_status = check_license()
    
    # Display license status
    st.header("License Status")
    
    if license_status.get("valid"):
        st.success("✅ Active License")
        
        # Display license details
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", "Active")
            if "customer_name" in license_status:
                st.metric("Customer", license_status["customer_name"])
        with col2:
            if "expires_at" in license_status:
                expires = datetime.fromisoformat(license_status["expires_at"].replace("Z", "+00:00"))
                days_left = (expires - datetime.now(expires.tzinfo)).days
                st.metric("Days Remaining", days_left)
                st.metric("Expires", expires.strftime("%Y-%m-%d"))
        
        # Display features
        if "features" in license_status and license_status["features"]:
            st.subheader("Enabled Features")
            for feature in license_status["features"]:
                st.write(f"- {feature}")
    else:
        st.error("🔒 Your license has expired. Please contact Nordic Secure for renewal.")
        
    # License activation section
    st.header("Activate License")
    
    with st.form("license_form"):
        license_key = st.text_input("Enter License Key", type="password")
        submitted = st.form_submit_button("Activate")
        
        if submitted and license_key:
            with st.spinner("Activating license..."):
                result = activate_license(license_key)
                
                if result.get("success"):
                    st.success("✅ License activated successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Activation failed: {result.get('message', 'Unknown error')}")

    # Footer
    st.markdown("---")
    st.markdown("**Nordic Secure License Manager** | Secure Offline License Management")

if __name__ == "__main__":
    main()
