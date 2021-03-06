from app import bloodrooster_app
from flask import render_template, request, redirect
from app.webapp import BloodRoosterWebApp


@bloodrooster_app.route("/")
def home():
    return redirect('/graph')


@bloodrooster_app.route("/graph", methods=['GET', 'POST'])
def graph():
    return render_template('index.html')


@bloodrooster_app.route("/graph_update", methods=['POST'])
def graph_update():
    """ Graph updating request handler """
    graph_data = ''
    webapp = BloodRoosterWebApp()
    if request.method == 'POST':
        graph_data = webapp.graph_update(request.get_json())
    return graph_data


@bloodrooster_app.route("/extended_info", methods=['POST'])
def extended_info():
    """ Node information request handler """
    webapp = BloodRoosterWebApp()
    object_data = webapp.get_extended_info(request.get_data())
    return object_data


@bloodrooster_app.route("/autocomplete", methods=['POST'])
def autocomplete():
    """ Node information request handler """
    webapp = BloodRoosterWebApp()
    object_data = webapp.autocomplete(request.get_json())
    return object_data
