import pandas as pd
import streamlit as st
import plotly.express as px

# Ref: https://towardsdatascience.com/streamlit-101-an-in-depth-introduction-fc8aad9492f2

# disable warnings
st.set_option('deprecation.showPyplotGlobalUse', False)

# fetch Airbnb data


@st.cache  # this will download the data and cache it for later use
def get_data():
    url = "http://data.insideairbnb.com/united-states/ny/new-york-city/2021-09-01/visualisations/listings.csv"
    return pd.read_csv(url)


df = get_data()


# Page Title and Subtitle
st.title("Streamlit 101: An in-depth introduction")
st.markdown("Welcome to this in-depth introduction to [...].")

st.header("Customary quote")
st.markdown("> I just love to go home, no matter where I am [...]")


# Display data in a df
st.header("Airbnb NYC listings: data at a glance")
st.markdown("The first five records of the Airbnb data we downloaded.")

st.dataframe(df.head())


# Additional Info
st.header("Caching our data")
st.markdown(
    "Streamlit has a handy decorator [`st.cache`](https://streamlit.io/docs/api.html#optimize-performance) to enable data caching.")
st.code("""
@st.cache
def get_data():
    url = "http://data.insideairbnb.com/united-states/ny/new-york-city/2021-09-01/visualisations/listings.csv"
    return pd.read_csv(url)
""", language="python")
st.markdown(
    "_To display a code block, pass in the string to display as code to [`st.code`](https://streamlit.io/docs/api.html#streamlit.code)_.")
with st.echo():
    st.markdown(
        "Alternatively, use [`st.echo`](https://streamlit.io/docs/api.html#streamlit.echo).")


# Display most expensive properties in a map
st.header("Where are the most expensive properties located?")
st.subheader("On a map")
st.markdown(
    "The following map shows the top 1% most expensive Airbnbs priced at $800 and above.")
# fetch price >=800 from the df in and display latitude and longitude, drop null values, display in a map
st.map(df.query("price>=800")[["latitude", "longitude"]].dropna(how="any"))


# Display most expensive properties in a table
st.subheader("In a table")
st.markdown("Following are the top five most expensive properties.")
# fetch price>=800, sort prices descending and display the head in a table
st.write(df.query("price>=800").sort_values("price", ascending=False).head())


# Display Avg price by room type in a table
st.header("Average price by room type")
st.write("You can also display static tables. As opposed to a data frame, with a static table you cannot sort by clicking a column header.")
# find price mean of room_type and sort descending
st.table(df.groupby("room_type").price.mean().reset_index()
         .round(2).sort_values("price", ascending=False)
         .assign(avg_price=lambda x: x.pop("price").apply(lambda y: "%.2f" % y)))


# Which hosts have the most properties listed?
st.header("Which host has the most properties listed?")
listingcounts = df.host_id.value_counts()
top_host_1 = df.query('host_id==@listingcounts.index[0]')
top_host_2 = df.query('host_id==@listingcounts.index[1]')
st.write(f"""**{top_host_1.iloc[0].host_name}** is at the top with {listingcounts.iloc[0]} property listings.
**{top_host_2.iloc[1].host_name}** is second with {listingcounts.iloc[1]} listings. Following are randomly chosen
listings from the two displayed as JSON using [`st.json`](https://streamlit.io/docs/api.html#streamlit.json).""")

# disply json
st.json({top_host_1.iloc[0].host_name: top_host_1
         [["name", "neighbourhood", "room_type", "minimum_nights", "price"]]
         .sample(2, random_state=4).to_dict(orient="records"),
         top_host_2.iloc[0].host_name: top_host_2
         [["name", "neighbourhood", "room_type", "minimum_nights", "price"]]
         .sample(2, random_state=4).to_dict(orient="records")})


# What is the distribution of property price?
# We display a histogram of property prices displayed as a Plotly chart using st.plotly_chart.
st.header("What is the distribution of property price?")
st.write("""Select a custom price range from the side bar to update the histogram below displayed as a Plotly chart using
[`st.plotly_chart`](https://streamlit.io/docs/api.html#streamlit.plotly_chart).""")
# slider with custom props that will affect the histogram
values = st.sidebar.slider("Price range", float(df.price.min()), float(
    df.price.clip(upper=1000.).max()), (50., 300.))
f = px.histogram(df.query(
    f"price.between{values}"), x="price", nbins=15, title="Price distribution")
f.update_xaxes(title="Price")
f.update_yaxes(title="No. of listings")
st.plotly_chart(f)


# Distribution of availability in various neighborhoods
st.header("What is the distribution of availability in various neighborhoods?")
st.write("Using a radio button restricts selection to only one option at a time.")
st.write("💡 Notice how we use a static table below instead of a data frame. \
Unlike a data frame, if content overflows out of the section margin, \
a static table does not automatically hide it inside a scrollable area. \
Instead, the overflowing content remains visible.")
# radio button for chosing the neighborhood
neighborhood = st.radio("Neighborhood", df.neighbourhood_group.unique())
# checkbox for including expensive listings
show_exp = st.checkbox("Include expensive listings")
show_exp = " and price<200" if not show_exp else ""

# function for displaying data based on the above options


@st.cache
def get_availability(show_exp, neighborhood):
    return df.query(f"""neighbourhood_group==@neighborhood{show_exp}\
        and availability_365>0""").availability_365.describe(
        percentiles=[.1, .25, .5, .75, .9, .99]).to_frame().T


# feed the fetched info into a table
st.table(get_availability(show_exp, neighborhood))
st.write("At 169 days, Brooklyn has the lowest average availability. At 226, Staten Island has the highest average availability.\
    If we include expensive listings (price>=$200), the numbers are 171 and 230 respectively.")
st.markdown(
    "_**Note:** There are 18431 records with `availability_365` 0 (zero), which I've ignored._")

df.query("availability_365>0").groupby("neighbourhood_group")\
    .availability_365.mean().plot.bar(rot=0).set(title="Average availability by neighborhood group",
                                                 xlabel="Neighborhood group", ylabel="Avg. availability (in no. of days)")
st.pyplot()


# Number of reviews
st.header("Properties by number of reviews")
st.write("Enter a range of numbers in the sidebar to view properties whose review count falls in that range.")

# inputs
minimum = st.sidebar.number_input("Minimum", min_value=0)
maximum = st.sidebar.number_input("Maximum", min_value=0, value=5)
# input validation for min and max
if minimum > maximum:
    st.error("Please enter a valid range")
else:
    # do the query
    df.query("@minimum<=number_of_reviews<=@maximum").sort_values("number_of_reviews", ascending=False)\
        .head(50)[["name", "number_of_reviews", "neighbourhood", "host_name", "room_type", "price"]]

st.write("486 is the highest number of reviews and two properties have it. Both are in the East Elmhurst \
    neighborhood and are private rooms with prices $65 and $45. \
    In general, listings with >400 reviews are priced below $100. \
    A few are between $100 and $200, and only one is priced above $200.")

# display Images
st.header("Images")
pics = {
    "Cat": "https://cdn.pixabay.com/photo/2016/09/24/22/20/cat-1692702_960_720.jpg",
    "Puppy": "https://cdn.pixabay.com/photo/2019/03/15/19/19/puppy-4057786_960_720.jpg",
    "Sci-fi city": "https://storage.needpix.com/rsynced_images/science-fiction-2971848_1280.jpg"
}
pic = st.selectbox("Picture choices", list(pics.keys()), 0)
st.image(pics[pic], use_column_width=True, caption=pics[pic])

st.markdown("## Party time!")
st.write("Yay! You're done with this tutorial of Streamlit. Click below to celebrate.")
btn = st.button("Celebrate!")
if btn:
    st.balloons()
