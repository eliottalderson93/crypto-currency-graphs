from django.shortcuts import render, HttpResponse, redirect, render_to_response
import requests, json
import pandas as pd
import numpy as np
from django.template import loader
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from bokeh.models import HoverTool
from django.core.serializers.json import DjangoJSONEncoder
import dateutil.relativedelta
import pprint
pp = pprint.PrettyPrinter(indent=4)

#the single page render

def graphs(request):
    context = {
        "plots" : []
    }

    #pp.pprint(testData)
    return render(request, 'graphs\graphs.html', context)

#the http response to the AJAX request for bokeh

def bokeh(request,firstCoin,secondCoin=False,begin = False,end = False):
    myAPICall = apiDataRequest(firstCoin = firstCoin,secondCoin = secondCoin, begin=begin,end=end)
    myPlot = coinDataOrganize(myAPICall)

    if(not myAPICall['oneCoin']):
        myDataframe = pandasCoinDataFrame(myPlot)
        myBokeh = bokehCoinPlot(myDataframe)
    else:
        myDataframe = pandasTimeDataFrame(myPlot)
        myBokeh = bokehTimePlot(myDataframe)
    
    print("end bokeh: ",myBokeh)
    return HttpResponse(template.render(context = context, request = request))#

#this function requests my node.js independent proxy server which communicates with the Nomics API

def apiDataRequest(firstCoin="BTC",secondCoin=False,begin=1525132800000,end=1527811199000): #defaults to may 2018
    apiCall = {}
    apiCall['inputs'] = True
    apiCall['oneCoin'] = True
    apiCall['firstCoin'] = None
    validFirstCoin = validateCoinTag(firstCoin)
    validSecondCoin = validateCoinTag(secondCoin)
    validBegin = validateUTC(begin)
    validEnd = validateUTC(end)
    print(" v firstCoin: ",validFirstCoin," v secondCoin: ",validSecondCoin," v begin: ",validBegin," v end ",validEnd)
    if(not validFirstCoin) and (not validSecondCoin):
        validFirstCoin = "BTC" #give a default graph
        apiCall['inputs'] = False
    elif not validFirstCoin:
        apiCall['inputs'] = False #we don't know what the frontend wants
        return apiCall
    elif not validSecondCoin: #default variable state is valid 
        pass 
    else:
        apiCall['oneCoin'] = False #this is a two coin graph

    
    if not validDates(validBegin,validEnd): #bad or reversed dates given by frontend
        apiCall['inputs'] = False
        return apiCall

    if not validBegin:
        apiCall['inputs'] = False
        validBegin=utcOneMonthAgo()

    if not validEnd:
        apiCall['inputs'] = False
        validEnd=utcNow()

    proxyUrl = "https://fierce-fortress-88237.herokuapp.com/"
    proxyUrl += str(validBegin)
    proxyUrl += "/"
    proxyUrl += str(validEnd)
    #add coin begin end to request
    #request the server
    response = requests.get(proxyUrl)
    apiCall['response'] = response.status_code
    print("URL::",proxyUrl)

    if response.status_code != 200: #checks if get was successful and breaks if not
        return apiCall

    data = response.json()
    len_currencies = int(len(data))
    currencyX = {}
    currencyY = {}

    if apiCall['oneCoin']:
        for i in range(0,len_currencies):

            if data[i]['currency'] == validFirstCoin: #find the single coin
                currencyX = data[i]
                break
            else:
                pass

    else: #two coins
        foundfirstCoin = False
        foundsecondCoin = False
        for i in range(0,len_currencies):

            if foundfirstCoin and foundsecondCoin:
                break

            if data[i]['currency'] == validFirstCoin:
                currencyX = data[i]
                foundfirstCoin = True
            elif data[i]['currency'] == validSecondCoin:
                currencyY = data[i]
                foundsecondCoin = True
            else:
                pass

    apiCall['firstCoin'] = currencyX
    if not apiCall['oneCoin']:
        apiCall['secondCoin'] = currencyY
    print("returned: ")
    return apiCall #return a dict with one or two relevant coins

#this function sorts the data into x and y plots

def coinDataOrganize(apiCall): #myData should be apiCall above
    plotData = {
        "x" : [None],
        "y" : [None],
        "date" : [None] #this is used only for coin vs coin plots
    }

    if(apiCall['firstCoin'] == None):
        return plotData

    if(not apiCall['oneCoin']):         #coin vs coin plot
        #validates the start and endpoints of the data. Do they lineup? trims off if they don't
        apiCall['firstCoin'], apiCall['secondCoin'] = lineUpRange(apiCall['firstCoin'], apiCall['secondCoin'])
        plotData['x'] = apiCall['firstCoin']['prices']
        plotData['y'] = apiCall['secondCoin']['prices']
        plotData['date'] = apiCall['firstCoin']['timestamps'] #same now for both coins
        plotData['xName'] = apiCall['firstCoin']['currency']
        plotData['yName'] = apiCall['secondCoin']['currency']
    else:
        #timeseries
        plotData['y'] = apiCall['firstCoin']['prices']
        plotData['x'] = apiCall['firstCoin']['timestamps']
        plotData['yName'] = apiCall['firstCoin']['currency']
        plotData['xName'] = "Time"

    return plotData

#these functions will create the pandas dataframe and do any statistical measurements

def pandasCoinDataFrame(plotData):
    dataFrame = pd.DataFrame(
        {'x': plotData['x'], 
         'y' : plotData['y'] , 
         'date' : plotData['date'], 
         'xLabel' : plotData['xName'],
         'yLabel' : plotData['yName']
         })
    print("dataframe:\n",dataFrame)
    return dataFrame

def pandasTimeDataFrame(plotData):
    dataFrame = pd.DataFrame(
        {'x': pd.to_datetime(plotData['x'],yearfirst = True), 
         'y' : plotData['y'] , 
         'date' : plotData['x'], 
         'xLabel' : plotData['xName'],
         'yLabel' : plotData['yName']
         })
    print("dataframe:\n",dataFrame)
    return dataFrame

#these functions use bokeh to build the responsive html element and returns it

def bokehTimePlot(dataFrame):#take pandas dataframe and make a bokeh plot price vs time
    TOOLTIPS = [
        ("Date", "@date"),
        ("Price", "$@y{0,0.00}")
    ]
    FORMAT = { "Date" : "datetime" }
    plot = figure(plot_width=1000, plot_height=700, x_axis_label = dataFrame['xLabel'][0], y_axis_label = dataFrame['yLabel'][0], title = "no title")
    plot.toolbar.logo = None
    plot.toolbar_location = None
    hover = HoverTool(tooltips=TOOLTIPS, mode = 'vline', formatters = FORMAT)
    plot.add_tools(hover)
    source = ColumnDataSource(dataFrame)
    #print("CDSx::",source.data['x'],"\nCDSy::",source.data['y'],"\nCDScols::",source.column_names)
    plot.line(x='x',y='y', source=source)
    #print("plot complete:",plot.select(dict(type=HoverTool))[0].tooltips)
    script, div = components(plot)
    context = {
        "script" : script,
        "div" : div
    }
    #print("context:", context)
    template = loader.get_template("graphs/ajaxGraph.html")
    return template

def bokehCoinPlot(dataFrame):#take pandas dataframe and make a bokeh plot coin vs coin
    TOOLTIPS = [
        ("Price X" , "$@x{0,0.00}"),
        ("Price Y" , "$@y{0,0.00}"),
        ("Date" , "@date")
    ]
    FORMAT = {"Date" : "datetime"}
    plot = figure(plot_width=1000, plot_height=700, x_axis_label = dataFrame['xLabel'][0], y_axis_label = dataFrame['yLabel'][0], title = "no title")
    plot.toolbar.logo = None
    plot.toolbar_location = None
    hover = HoverTool(tooltips=TOOLTIPS, mode = 'vline', formatters = FORMAT)
    plot.add_tools(hover)
    source = ColumnDataSource(dataFrame)
    print("CDSx::",source.data['x'],"\nCDSy::",source.data['y'],"\nCDScols::",source.column_names)
    plot.scatter(x='x',y='y', source=source)
    print("plot complete:",plot.select(dict(type=HoverTool))[0].tooltips)
    script, div = components(plot)
    context = {
        "script" : script,
        "div" : div
    }
    template = loader.get_template("graphs/ajaxGraph.html")
    return template #returns a html bokeh plot

#HELPER functions
def validateCoinTag(coin):
    if type(coin) != type("String"):
        return False
    else:
        coin = coin.upper()
        return coin

def validateUTC(date):
    if type(date) != type(1):
        return False
    elif len(str(date)) != len(str(1525132800000)):
        return False
    else:
        return date

def validDates(begin,end):
    if begin > end:
        return False
    else:
        return True

def lineUpRange(obj1,obj2): #validates range if cryptocurrencies have different range

    if obj1['timestamps'][0] != obj2['timestamps'][0]: #need to pop off datapoints from earlier coin
        obj1['timestamps'],obj2['timestamps'] = equalizeArrays(obj1['timestamps'],obj2['timestamps'])
        obj1['prices'],obj2['prices'] = equalizeArrays(obj1['prices'],obj2['prices'])

    obj1End = len(obj1['timestamps'])-1 #size has been altered in above logic block
    obj2End = len(obj2['timestamps'])-1

    if obj1['timestamps'][obj1End] != obj2['timestamps'][obj2End]: #need to pop off datapoints from later coin
        obj1['timestamps'],obj2['timestamps'] = equalizeArraysBack(obj1['timestamps'],obj2['timestamps'])
        obj1['prices'],obj2['prices'] = equalizeArraysBack(obj1['prices'],obj2['prices'])

    return obj1,obj2

def utcNow():
    return (np.datetime64(datetime.datetime.now()).astype('uint64') / 1e6).astype('uint32')

def utcOneMonthAgo():
    return (np.datetime64(datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=-1)).astype('uint64') / 1e6).astype('uint32')

def utcOneWeekAgo():
    return (np.datetime64(datetime.datetime.now() + dateutil.relativedelta.relativedelta(weeks=-1)).astype('uint64') / 1e6).astype('uint32')

def utcOneYearAgo():
    return (np.datetime64(datetime.datetime.now() + dateutil.relativedelta.relativedelta(years=-1)).astype('uint64') / 1e6).astype('uint32')

def axis(array,key_str): #this function searches a passed in array for the key_str and returns the array of only those values
    axis_var = [] #can be x or y usually
    for obj in array:
        axis_var.append(obj[key_str])
    return axis_var

def equalizeArrays(arr1,arr2):
    while (len(arr1) > len(arr2)):
        arr1.pop(0) #pops from FRONT of array of data with larger size. 
                    #this function is because we dont want to compare coins when the later one was non-existent
    while(len(arr2) > len(arr1)):
        arr2.pop(0)
    return arr1, arr2

def equalizeArraysBack(arr1,arr2):
    end1 = len(arr1)-1
    end2 = len(arr2)-1
    while (len(arr1) > len(arr2)):
        arr1.pop(end1) #pops from END of array of data with larger size. 
                    #this function is because we dont want to compare coins when the ealier one was non-existent
    while(len(arr2) > len(arr1)):
        arr2.pop(end2)
    return arr1, arr2

def datetime(x):
    return np.array(x, dtype=np.datetime64)

def parseArr(jsonArr):
    x = []
    y = []
    date = []
    for point in jsonArr:
        x.append(point['x'])
        y.append(point['y'])
        date.append(point['date'])
    return x, y, date 
