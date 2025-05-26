from streamlit.web.server.oidc_mixin import TornadoOAuth2App, TornadoOAuth
import tornado.web

class TornadoOAuth2AppWithEntraAuth(TornadoOAuth2App):
    
    
    def authorize_access_token(
        self, request_handler: tornado.web.RequestHandler, **kwargs
    ):
        return super().authorize_access_token(
            request_handler, claims_options={}
        )

class TornadoOAuthWithEntra(TornadoOAuth):
    oauth2_client_cls = TornadoOAuth2AppWithEntraAuth

import streamlit.web.server.oauth_authlib_routes

streamlit.web.server.oauth_authlib_routes.TornadoOAuth = TornadoOAuthWithEntra

import streamlit as st
# Access code dialog
@st.dialog("Teacher Login")
def teacher_login_dialog():
    # Login section
    with st.columns((0.2, 2, 0.2))[1]:
        st.markdown("Continue with your email:")
        if st.button("Log In", type="primary", use_container_width=True):
            st.login("auth0")
        st.markdown("Or login through:")
        if st.button("Google", type="primary", use_container_width=True):
            st.login("google")
        if st.button("Microsoft", type="primary", use_container_width=True):
            st.login("microsoft")
    st.stop()  