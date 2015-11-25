var express = require('express');
var http = require('http');
var config = require('./config/config.js');
var glob = require('glob');

var app = express();
var server = http.createServer(app);

require('./config/express.js')(app, server, config);

server.listen(config.port);
