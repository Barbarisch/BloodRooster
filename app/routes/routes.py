from app import bloodrooster_app
from flask import render_template, request, redirect, session
from app.webapp import BloodRoostrWebApp


@bloodrooster_app.route("/")
def home():
    return redirect('/graph')


@bloodrooster_app.route("/graph", methods=['GET', 'POST'])
def graph():
    return render_template('index.html')


@bloodrooster_app.route("/graph_update", methods=['POST'])
def graph_update():
    graph_data = ''
    webapp = BloodRoostrWebApp()
    if request.method == 'POST':
        graph_data = webapp.graph_update(request.get_json())
    return graph_data


@bloodrooster_app.route("/extended_info", methods=['POST'])
def extended_info():
    webapp = BloodRoostrWebApp()
    object_data = webapp.get_extended_info(request.get_data())
    return object_data
