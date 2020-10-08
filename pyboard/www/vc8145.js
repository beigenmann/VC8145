// var output;

function init() {
  // output = setValue("output");
  startWebSocket();
}

function startWebSocket() {
  var wsUri = "ws://" + window.location.hostname;
  //var wsUri = "ws://espressif.lan";
  console.log("Connection to " + wsUri + "...");
  websocket = new WebSocket(wsUri);
  websocket.onopen = function (evt) {
    onOpen(evt);
  };
  websocket.onclose = function (evt) {
    onClose(evt);
  };
  websocket.onmessage = function (evt) {
    onMessage(evt);
  };
  websocket.onerror = function (evt) {
    onError(evt);
  };
}

function onOpen(evt) {
  console.log("<strong>-- CONNECTED --</strong>");
  //SendMsg("Hello world :)");
  //SendMsg("This is a WebSocket test");
  //SendMsg("(with a text frame encoded in UTF-8)");
  //setTimeout( function() { websocket.close() }, 5000 )
}

function onClose(evt) {
  console.log("<strong>-- DISCONNECTED --</strong>");
}
freq_count = 0;
function onMessage(evt) {
  try {
    //console.log('MSG FROM SERVER' , evt.data  );
    var data = JSON.parse(evt.data);

    if (data["second"].value.includes("??")) {
      setValue("meterValue1", "");
      setValue("unit1", "");
    } else {
      setValue("meterValue1", data["second"].sign + data["second"].value);
      setValue("unit1", data["second"].pre_unit + data["second"].unit);
    }
    setValue("mode2", data["first"].mode);
    _mode = " ";
    if (data["first"].mode == "Capacitance") {
      _mode = "H";
    }
    if (data["first"].mode == "Diode") {
      _mode = "D";
    }
    if (data["first"].mode == "Voltage AC") {
      _mode = "F";
    }
    if (data["first"].mode == "Voltage DC") {
      _mode = "E";
    }
    setValue("mode1", _mode);
    firstValue = data["first"].sign + data["first"].value;
    setValue("meterValue2", firstValue);
    firstUnit = data["first"].pre_unit + data["first"].unit;
    setValue("unit2", firstUnit);
    setValue("range", data["first"].autorange);
    setValue("hold", data["first"].hold);
    setValue("rel", data["first"].rel);
    setValue("minmax", data["first"].minmax);
    document.getElementById("analog_bar").value = data["status"].value - 0x7f;
    freq_count++;
    freq_count = freq_count % 50;
    if (freq_count == 1) {
      updateChart(data["time"], firstValue, firstUnit, data["first"].mode);
    }

    // console.log("MSG FROM SERVER", data["status"].value);
  } catch (e) {}
}
function setValue(id, value) {
  if (value == null || value.length == 0) {
    value = "&nbsp;";
  }
  var element = document.getElementById(id);
  if (element != null) {
    element.innerHTML = value;
  } else {
    console.log(id, element);
  }
}

function onError(evt) {
  console.log('ERROR : <span style="color: red;">' + evt.data + "</span>");
}

function SendMsg(msg) {
  console.log('MSG TO SERVER : <span style="color: green;">' + msg + "</span>");
  websocket.send(msg);
}
function onRange() {
  console.log("onRange");
  websocket.send('{ "msg":"range"}');
}
function onHold() {
  console.log("onHold");
  websocket.send('{ "msg":"hold"}');
}

function onRel() {
  console.log("onRel");
  websocket.send('{ "msg":"rel"}');
}

function onMinMax() {
  console.log("onMinMax");
  websocket.send('{ "msg":"min_max"}');
}

function onSelect() {
  console.log("onSelect");
  websocket.send('{ "msg":"select"}');
}

function on2ndView() {
  console.log("on2ndView");
  websocket.send('{ "msg":2nd_view"}');
}

function onTimer() {
  console.log("onTimer");
  websocket.send('{ "msg":"timer"}');
}
tabName = "meter";
function toggleMeterChart(evt) {
  if (tabName == "chart") {
    tabName = "meter";
    document.getElementById("toggleMeterChart").textContent = "Chart";
  } else {
    tabName = "chart";
    document.getElementById("toggleMeterChart").textContent = "Meter";
  }
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"

  tablinks = document.getElementsByClassName("tablinks");

  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}
window.addEventListener("load", init, false);
var currentValue = 0;
var chartColors = {
  red: "rgb(255, 99, 132)",
  orange: "rgb(255, 159, 64)",
  yellow: "rgb(255, 205, 86)",
  green: "rgb(75, 192, 192)",
  blue: "rgb(54, 162, 235)",
  purple: "rgb(153, 102, 255)",
  grey: "rgb(201, 203, 207)",
};

function onRefresh(chart) {
  chart.config.data.datasets.forEach(function (dataset) {
    dataset.data.push({
      x: Date.now(),
      y: currentValue, // randomScalingFactor(),
    });
  });
}

var color = Chart.helpers.color;
var config = {
  type: "line",
  data: {
    datasets: [
      {
        label: "Dataset 1 (linear Cube)",
        backgroundColor: color(chartColors.red).alpha(0.5).rgbString(),
        borderColor: chartColors.blue,
        fill: false,
        cubicInterpolationMode: "monotone",
        data: [],
      },
    ],
  },
  options: {
    maintainAspectRatio: false,
    title: {
      display: true,
      text: "VC8145",
    },
    scales: {
      xAxes: [
        {
          type: "realtime",
          realtime: {
            duration: 300000,
            delay: 0,
          },
          time: {
            displayFormats: {
              millisecond: "",
              second: "HH:mm:ss",
              minute: "mm",
              hour: "",
            },
          },
        },
      ],
      yAxes: [
        {
          scaleLabel: {
            display: true,
            labelString: "value",
          },
        },
      ],
    },
    tooltips: {
      mode: "nearest",
      intersect: false,
    },
    hover: {
      mode: "nearest",
      intersect: false,
    },
  },
};

window.onload = function () {
  var ctx = document.getElementById("_Chart").getContext("2d");
  window._Chart = new Chart(ctx, config);
};

// your event listener code - assuming the event object has the timestamp and value properties
function updateChart(timestamp, value, unit, mode) {
  currentValue = Number.parseFloat(value);
  window._Chart.config.data.datasets.forEach(function (dataset) {
    dataset.label = mode + " [" + unit + "]";
    dataset.data.push({
      x: Date.now(),
      y: currentValue,
    });
  });
  window._Chart.options.scales.yAxes[0].scaleLabel.labelString =
    mode + " [" + unit + "]";
  window.myChart.update();
}
