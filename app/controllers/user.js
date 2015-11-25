var express = require('express');
var router = express.Router();
var docker = require('./../utils/docker.js');

module.exports = function(app) {
  app.use('/', router);
};

router.route('/login').all(function(req, res, next) {
  if (req.session.username) {
    return res.redirect('/');
  }
  next();
}).post(function(req, res, next) {
  var data = {
    cmd: 'auth',
    username: req.body.username,
    password: req.body.password
  };
  docker.sendData(data, function(d) {
    var auth = d.auth;
    if (auth) {
      req.session.username = req.body.username;
      req.session.password = req.body.password;
      res.redirect('/getRepoList');
    } else {
      req.flash('login', '아이디 또는 비밀번호를 확인해 주세요');
      res.redirect('/');
    }
  });
});

router.route('/logout').all(function(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/');
  }
  next();
}).post(function(req, res, next) {
  if (req.session) {
    req.session.destroy(function() {
      res.redirect('/');
    });
  }
});
