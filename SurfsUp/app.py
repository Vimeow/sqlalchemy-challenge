# Design An Climate App

# Import dependencies
import re
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

#################################################
# Create an app (Flask Setup)
#################################################

app = Flask(__name__)
# to keep order of sorted dictionary passed to jsonify() function
app.json.sort_keys = False

#################################################
# (1)
# Start at the homepage.
# List all the available routes.
#################################################


@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start(YYYY-MM-DD)<br/>"
        f"/api/v1.0/start/end(YYYY-MM-DD/YYYY-MM-DD)<br/>"
    )

#################################################
# (2)
# Convert the query results to a dictionary by using date as the key and prcp as the value.
# Return the JSON representation of the dictionary.
#################################################


@app.route("/api/v1.0/precipitation")
def precipitation():

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query measurement
    results = (session.query(measurement.date, measurement.prcp)
               .order_by(measurement.date). all())

    session.close()

    # Create a dictionary
    date_precipitation = []
    for row in results:
        dt_dict = {}
        dt_dict["date"] = row.date
        dt_dict["precipitation"] = row.prcp
        date_precipitation.append(dt_dict)

    return jsonify(date_precipitation)

#################################################
# (3)
# Return a JSON list of stations from the dataset.
#################################################


@app.route("/api/v1.0/stations")
def stations():

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query all stations
    results = session.query(station.name).all()

    session.close()

    # Convert list of tuples into normal list
    station_list = list(np.ravel(results))

    return jsonify(station_list)

#################################################
# (4)
# Query the dates and temperature observations of the most-active station for the previous year of data.
# Return a JSON list of temperature observations for the previous year.
#################################################


@app.route("/api/v1.0/tobs")
def tobs():

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date in the data set.
    most_recent_date = (session.query(measurement.date)
                        .order_by(measurement.date.desc())
                        .first())

    # Convert date to datetime object
    most_recent_date_str = str(most_recent_date)
    most_recent_date_str = re.sub("'|,", "", most_recent_date_str)
    most_recent_date_obj = dt.datetime.strptime(
        most_recent_date_str, '(%Y-%m-%d)')

    # Calculate the date one year from the last date in data set.
    one_year_ago_date = dt.date(most_recent_date_obj.year, most_recent_date_obj.month,
                                most_recent_date_obj.day) - dt.timedelta(days=366)

    # Perform a query to retrieve the most active stations (the station with the most rows).
    year_tobs = (session.query(measurement.station)
                 .group_by(measurement.station)
                 .order_by(func.count(measurement.station).desc())
                 .all())

    most_active_station = year_tobs[0][0]

    # Query the dates and temperature observations of the most-active station for the previous year of data
    results = (session.query(measurement.station, measurement.date, measurement.tobs)
               .filter(measurement.date > one_year_ago_date)
               .filter(measurement.station == most_active_station)
               .all())

    session.close()

    # Return a JSON list of temperature observations for the previous year.
    tobs_list = []
    for result in results:
        line = {}
        line["Station"] = result[0]
        line["Date"] = result[1]
        line["Temperature"] = int(result[2])
        tobs_list.append(line)

    return jsonify(tobs_list)

#################################################
# (5)
# Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.
#################################################

# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.


@app.route("/api/v1.0/<start>")
def start(start):

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query the min, avg, max temperature from the start date
    results = (session.query(func.min(measurement.tobs),
                             func.avg(measurement.tobs),
                             func.max(measurement.tobs))
               .filter(measurement.date >= start).all())

    session.close()

    # Return a JSON list
    tobs_list = []
    for result in results:
        line = {}
        line["Start date"] = start
        line["Minimum temperature"] = results[0][0]
        line["Average temperature"] = round((results[0][1]), 1)
        line["Maximum temperature"] = results[0][2]
        tobs_list.append(line)

    return jsonify(tobs_list)


# For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query the min, avg, max temperature between the start and end date
    results = (session.query(func.min(measurement.tobs),
                             func.avg(measurement.tobs),
                             func.max(measurement.tobs))
               .filter(measurement.date <= end)
               .filter(measurement.date >= start).all())

    session.close()

    # Return a JSON list
    tobs_list = []
    for result in results:
        line = {}
        line["Start date"] = start
        line["End date"] = end
        line["Minimum temperature"] = results[0][0]
        line["Average temperature"] = round((results[0][1]), 1)
        line["Maximum temperature"] = results[0][2]
        tobs_list.append(line)

    return jsonify(tobs_list)


# Launching the app
if __name__ == "__main__":
    app.run(debug=True)
