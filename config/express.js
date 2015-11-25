var express = require('express');
var glob = require('glob');
var cookieParser = require('cookie-parser');
var bodyParser = require('body-parser');
var session = require('express-session');
var flash = require('connect-flash');

module.exports = function(app, server, config) {
  app.set('views', config.root + '/app/views');
  app.set('view engine', 'jade');
  app.use('/assets', express.static(config.root + '/public'));

  /* debug */
  app.disable('view cache');

  app.use(bodyParser.json());
  app.use(bodyParser.urlencoded({ extended: true }));
  app.use(cookieParser('asdkasjfadklhfaslkdhsakld'));

  app.use(session({
    secret: 'asdopjasdpasjdasid',
    cookie: {
      maxAge: 1000*60*60*24*7
    },
    resave: false,
    saveUninitialized: false
  }));
  app.use(flash());

  var controllers = glob.sync(config.root + '/app/controllers/**/*.js');
  controllers.forEach(function(controller) {
    require(controller)(app);
  });
};

