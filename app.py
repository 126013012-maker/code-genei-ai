import streamlit as st

st.title("My Streamlit App")
st.write("Hello, world!")
st.write("This is a simple Streamlit application.")
st.text("This is a text element.")

st.slider("Select a value", 0, 100, 50)

if st.button("Click me"):
    st.write("Button clicked!")

number = st.number_input("Enter a number", 0, 100, 50)
st.write("You entered:", number)