var net = require('net');
var config = require('./../../config/config.js');
exports.sendData = function(data, fn) {
  var client = net.connect({
    host: config.docker.host,
    port: config.docker.port
  }, function() {
    client.write(JSON.stringify(data));
  });

  var d = '';
  client.on('data', function(data) {
    d += data;
  });
  client.on('end', function() {
    try {
      fn(JSON.parse(d));
    } catch(e) {
      console.error(e);
    }
  });
  client.on('error', function(exc) {
    console.log('docker socket ignoring exception ', exc);
  });
};

exports.run = function(data, fn) {
  var client = net.connect({
    host: config.docker.host,
    port: config.docker.runPort
  }, function() {
    client.write(JSON.stringify(data));
  });

  var d = '';
  client.on('data', function(data) {
    d += data;
  });
  client.on('end', function() {
    try {
      console.log(d);
      fn(JSON.parse(d));
    } catch(e) {
      console.error(e);
    }
  });
  client.on('error', function(exc) {
    console.log('docker socket ignoring exception ', exc);
  });
};
