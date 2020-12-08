import os
import requests
import urllib.parse, urllib.request, json

from flask import redirect, render_template, request, session
from functools import wraps

def apidict(school):
    return {
        'sat75thmath': float(school['2018.admissions.sat_scores.75th_percentile.math']) if school['2018.admissions.sat_scores.75th_percentile.math'] else None,
        'satmidptmath': float(school['2018.admissions.sat_scores.midpoint.math']) if school['2018.admissions.sat_scores.midpoint.math'] else None,
        'act25thcum': float(school['2018.admissions.act_scores.25th_percentile.cumulative']) if school['2018.admissions.act_scores.25th_percentile.cumulative'] else None,
        'act25theng': float(school['2018.admissions.act_scores.25th_percentile.english']) if school['2018.admissions.act_scores.25th_percentile.english'] else None,
        'name': school['school.name'],
        'actmidptcum': float(school['2018.admissions.act_scores.midpoint.cumulative']) if school['2018.admissions.act_scores.midpoint.cumulative'] else None,
        'sat75thread': float(school['2018.admissions.sat_scores.75th_percentile.critical_reading']) if school['2018.admissions.sat_scores.75th_percentile.critical_reading'] else None,
        'satmidptread': float(school['2018.admissions.sat_scores.midpoint.critical_reading']) if school['2018.admissions.sat_scores.midpoint.critical_reading'] else None,
        'act25thmath': float(school['2018.admissions.act_scores.25th_percentile.math']) if school['2018.admissions.act_scores.25th_percentile.math'] else None,
        'act75thmath': float(school['2018.admissions.act_scores.75th_percentile.math']) if school['2018.admissions.act_scores.75th_percentile.math'] else None,
        'admission_rate': float(school['2018.admissions.admission_rate.overall']) if school['2018.admissions.admission_rate.overall'] else None,
        'sataverage': float(school['2018.admissions.sat_scores.average.by_ope_id']) if school['2018.admissions.sat_scores.average.by_ope_id'] else None,
        'actmidptmath': float(school['2018.admissions.act_scores.midpoint.math']) if school['2018.admissions.act_scores.midpoint.math'] else None,
        'sataverage': float(school['2018.admissions.sat_scores.average.overall']) if school['2018.admissions.sat_scores.average.overall'] else None,
        'sat25thmath': float(school['2018.admissions.sat_scores.25th_percentile.math']) if school['2018.admissions.sat_scores.25th_percentile.math'] else None,
        'sat25thread': float(school['2018.admissions.sat_scores.25th_percentile.critical_reading']) if school['2018.admissions.sat_scores.25th_percentile.critical_reading'] else None,
        'id': int(school['id']),
        'act75theng': float(school['2018.admissions.act_scores.75th_percentile.english']) if school['2018.admissions.act_scores.75th_percentile.english'] else None,
        'actmidpteng': float(school['2018.admissions.act_scores.midpoint.english']) if school['2018.admissions.act_scores.midpoint.english'] else None,
        'act75thcum': float(school['2018.admissions.act_scores.75th_percentile.cumulative']) if school['2018.admissions.act_scores.75th_percentile.cumulative'] else None,
        'sat25thwrite': float(school['2018.admissions.sat_scores.25th_percentile.writing']) if school['2018.admissions.sat_scores.25th_percentile.writing'] else None,
        'sat75thwrite': float(school['2018.admissions.sat_scores.75th_percentile.writing']) if school['2018.admissions.sat_scores.75th_percentile.writing'] else None,
        'satmidptwrite': float(school['2018.admissions.sat_scores.midpoint.writing']) if school['2018.admissions.sat_scores.midpoint.writing'] else None,
        'act25thwrite': float(school['2018.admissions.act_scores.25th_percentile.writing']) if school['2018.admissions.act_scores.25th_percentile.writing'] else None,
        'act75thwrite': float(school['2018.admissions.act_scores.75th_percentile.writing']) if school['2018.admissions.act_scores.75th_percentile.writing'] else None,
        'actmidptwrite': float(school['2018.admissions.act_scores.midpoint.writing']) if school['2018.admissions.act_scores.midpoint.writing'] else None
    }

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def lookup(name):
    try:
        api_key = 'WDRJDCO5nn7TKjj3bClqecdGTZyx34pe4XuzSYzn'
        school_name=urllib.parse.quote_plus(name)
        url = f'https://api.data.gov/ed/collegescorecard/v1/schools.json?school.name={school_name}&fields=id,school.name,2018.admissions&per_page=100&api_key={api_key}'
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        schools = response.json()['results']
        results = []
        for school in schools:
            results.append(apidict(school))
        return results
    except (KeyError, TypeError, ValueError):
        return None

def lookup_by_id(ids):
    api_key = 'WDRJDCO5nn7TKjj3bClqecdGTZyx34pe4XuzSYzn'
    results=[]
    for i in ids:
        url = f'https://api.data.gov/ed/collegescorecard/v1/schools.json?id={i}&fields=id,school.name,2018.admissions&per_page=100&api_key={api_key}'
        response = requests.get(url)


        school = response.json()['results'][0]
        results.append(apidict(school))
    return results

def lookup_by_stats(stats):
    query = ''
    if(stats['sat']):
        up = stats['sat']+250 if stats['sat']+250 < 1600 else 1600
        low = stats['sat']-250 if stats['sat']-250 > 400 else 400
        query+=f'2018.admissions.sat_scores.average.overall__range={low}..{up}'
    if(stats['sat'] and stats['act']):
        query+='&'
    if(stats['act']):
        up = stats['act']+3 if stats['act']+3 < 36 else 36
        low = stats['act']-3 if stats['act']-3 > 1 else 1
        query+=f'2018.admissions.act_scores.midpoint.cumulative__range={low}..{up}'
    try:
        api_key = 'WDRJDCO5nn7TKjj3bClqecdGTZyx34pe4XuzSYzn'
        url = f'https://api.data.gov/ed/collegescorecard/v1/schools.json?{query}&fields=id,school.name,2018.admissions&per_page=100&api_key={api_key}'
        print(url)
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        schools = response.json()['results']
        results = []
        for school in schools:
            results.append(apidict(school))
        return results
    except (KeyError, TypeError, ValueError):
        return None