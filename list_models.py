import google.generativeai as genai
import streamlit as st

# Configure your API key
genai.configure(api_key="AIzaSyC1IaE5_GHBzQxywhCxOpH9YaefWLntBD0")  # use your key

# List all available models
models = genai.list_models()
for model in models:
    print(f"Model Name: {model.name}")
    print(f"  Type: {model.model_type}")
    print(f"  Supported Methods: {model.supported_generation_methods}")
    print("-" * 50)
