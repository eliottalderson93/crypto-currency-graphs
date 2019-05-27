$(document).ready(function () {
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    //autocomplete attempt failed due to CSS styling of ui-menu-item
    var coinNames = [];
    $.ui.autocomplete.prototype._renderItem = function (ul, item) {
        //console.log("ul children: ", ul.children());
        //console.log("item: ", item);
        return $("<li><a>")
            .data("item.autocomplete", item)
            .append(item.label + "</a></li>")
            .appendTo(ul);
    };
    $.ui.autocomplete.prototype._renderMenu = function (ul, items) {
        //console.log("ul rendermenu",ul,items);
        ul.addClass('menu-list');
        var self = this;
        $.each(items, function (index, item) {
            self._renderItem(ul, item);
        });
    }
    $.ajax({
        url: "https://127.0.0.1/api/",
        type: "GET",
        crossDomain: true,
        dataType: "json",
        success: function (response) {
            response.forEach(function (element) {
                coinNames.push(element['id']);
            });
            //console.log("coinNames: ",coinNames);
            $( "#coinName" ).autocomplete({
                source : coinNames,
                minLength : 2,
                classes: {
                    "ui-autocomplete": "box is-white dropdown",
                },
                response: function( event, ui ) {
                    while(ui['content'].length > 10){
                        ui['content'].pop();
                    }
                }
            });
        },
        error: function(xhr, status) {
            console.log("error cannot autocomplete");
            console.log(this);
        }
    });
    $('#customTime').submit(function(e){
        var coinParam = $('#coinName').val();
        var beginParam = $('#beginTime').val();
        var endParam = $('#endTime').val();
        var coinUrl;
        var beginUrl;
        var endUrl;
        var errorFlag = true;
        var messages = {
            coin : null,
            begin : null,
            end : null,
        }
        var url = "http://127.0.0.1/bokeh";
        //console.log("parameters: ",coinParam,' : ',beginParam,' : ',endParam);
        if(!(validateArray(coinParam,coinNames))){
            errorFlag = false;
            messages['coin'] = "No Data. Please try another coin.";
            //throw error coin param
        }
        if(endParam.length === 0 && beginParam.length === 0){ //this is the case for the whole coin
            url += "/" + String(coinParam).toLowerCase().replace(/\s/g, '');
                  
        
        }else{ //this is the case for two time parameters
            console.log("time case");
            if(isValidDate(beginParam)){
                beginUrl = "/" + String(epochTime(beginParam)) + "/";
            }
            else{
                errorFlag = false;
                messages['begin'] = "Please enter a valid begin date.";
                //throw error begin param
            }
            if(isValidDate(endParam)){
                endUrl = String(epochTime(endParam));
                if(epochTime(beginParam) >= epochTime(endParam)){
                    errorFlag = false;
                    messages['begin'] = "Your begin date is later than your end date";
                    //throw error invalid times
                }
            }
            else{
                errorFlag = false;
                messages['end'] = "Please enter a valid end date.";
                //throw error end param
            }
            url += "/" + String(coinParam).toLowerCase().replace(/\s/g, '') + beginUrl + endUrl;
        }
        if(errorFlag){
            console.log("making request:",url);
            $.ajax({
                type: "GET",
                url: url,
                success: function(response)
                {
                    //console.log(response);
                    $('#graphs').html(response)
                }
            });
        }
        else{
            $('#coinError').text(messages['coin']);
            $('#beginError').text(messages['begin']);
            $('#endError').text(messages['end']);
            $('#coinName').val(coinParam);
            $('#beginTime').val(beginParam);
            $('#endTime').val(endParam);
        }
        return false;
    });
    //http://18.220.161.116:8000
    $('#bitcoin').click(function () {
        $.ajax({
            url: "http://127.0.0.1:8000/bokeh/BTC",
            type: "GET",
            crossDomain: true,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                $('#graphs').html(response)
            },
            error: function (xhr, status) {
                console.log("error xhr: ", xhr.status, "status: ", status);
            }
        });
    });
    $('#tether').click(function () {
        $.ajax({
            url: "http://127.0.0.1:8000/bokeh/USDT",
            type: "GET",
            crossDomain: true,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                $('#graphs').html(response)
            },
            error: function (xhr, status) {
                console.log("error xhr: ", xhr.status, "status: ", status);
            }
        });        
    });
    $('#tvb').click(function () {
        $.ajax({
            url: "http://127.0.0.1:8000/bokeh/USDT/BTC/1483228800000/1514764800000",
            type: "GET",
            crossDomain: true,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                $('#graphs2').html(response)
            },
            error: function (xhr, status) {
                console.log("error xhr: ", xhr.status, "status: ", status);
            }
        });
    });
    $('#btc_timed').click(function () {
        $.ajax({
            url: "http://127.0.0.1:8000/bokeh/time/BTC/1483228800000/1514764800000",
            type: "GET",
            crossDomain: true,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                $('#graphs').html(response);
            },
            error: function (xhr, status) {
                console.log("error xhr: ", xhr.status, "status: ", status);
            }
        });
    });
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function validateArray(myValue,arr){
        if(typeof(arr) != typeof(['array'])){
            return false;
        }
        for (var i = 0;i<arr.length;i++){
            if(arr[i].toLowerCase() === myValue.toLowerCase()){
                return true;
            }
        }
        return false;
    }
    function epochTime(timeString){
        return new Date(timeString).valueOf();
    }
    function isValidDate(dateString) {
        var regEx = /^\d{4}-\d{2}-\d{2}$/;
        if(!dateString.match(regEx)) return false;  // Invalid format
        var d = new Date(dateString);
        if(Number.isNaN(d.getTime())) return false; // Invalid date
        return d.toISOString().slice(0,10) === dateString;
    }
});