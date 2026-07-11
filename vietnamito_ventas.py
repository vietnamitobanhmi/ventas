streamlit.errors.StreamlitAPIException: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:
File "/mount/src/ventas/vietnamito_ventas.py", line 3093, in <module>
    render_dashboard(df)
File "/mount/src/ventas/vietnamito_ventas.py", line 2728, in render_dashboard
    e_desc = st.text_area("🇪🇸 Descripción:", value=prod.get("descripcion") or "", key=f"ed_{prod['id']}", height=60)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.12/site-packages/streamlit/runtime/metrics_util.py", line 409, in wrapped_func
    result = non_optional_func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.12/site-packages/streamlit/elements/widgets/text_widgets.py", line 508, in text_area
    raise StreamlitAPIException(
