var express = require('express');
var router = express.Router();
var docker = require('./../utils/docker.js');

module.exports = function(app) {
  app.use('/', router);
};

router.route('/getRepoList').all(function(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/');
  }
  next();
}).get(function(req, res, next) {
  var data = {
    cmd: 'getRepoList',
    username: req.session.username,
    password: req.session.password
  };
  docker.sendData(data, function(d) {
    res.render('repo_list', {
      repoList: d
    });
  });
});

router.route('/getRepo').all(function(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/');
  }
  next();
}).post(function(req, res, next) {
  var url = req.body.url;
  var data = {
    cmd: 'getRepo',
    username: req.session.username,
    password: req.session.password,
    url: url
  };
  docker.sendData(data, function(d) {
    res.json(d);
  });
});

router.route('/getFile').all(function(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/');
  }
  next();
}).post(function(req, res, next) {
  var path = req.body.path;
  var filename = req.body.filename;
  var data = {
    cmd: 'getFile',
    username: req.session.username,
    password: req.session.password,
    path: path,
    filename: filename
  };
  docker.sendData(data, function(d) {
    res.json(d.content);
  });
});

router.route('/commit').all(function(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/');
  }
  next();
}).post(function(req, res, next) {
  var content = req.body.content;
  var path = req.body.path;
  var filename = req.body.filename;
  var url = req.body.url;
  var commitMsg = req.body.commitMsg;
  var data = {
    cmd: 'commit',
    content: content,
    path: path,
    filename: filename,
    url: url,
    username: req.session.username,
    password: req.session.password,
    commitMsg: commitMsg
  };
  docker.sendData(data, function(d) {
    if (d.stdout) {
      d.stdout = d.stdout.replace(/\n|\r\n|\r/g, '<br>');
    }
    res.json(d);
  });
});

router.route('/newRepo').all(function(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/');
  }
  next();
}).post(function(req, res, next) {
  var repoName = req.body.repoName;
  var repoDesc = req.body.repoDesc;
  var data = {
    cmd: 'newRepo',
    username: req.session.username,
    password: req.session.password,
    repoName: repoName,
    repoDesc: repoDesc
  };
  docker.sendData(data, function(d) {
    res.send(d);
  });
});
    
