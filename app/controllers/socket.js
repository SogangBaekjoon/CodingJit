var express = require('express');
var router = express.Router();
var docker = require('./../utils/docker.js');

module.exports = function(app) {
  app.use('/', router);
};

router.route('/run').all(function(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/');
  }
  next();
}).post(function(req, res, next) {
  var content = req.body.content;
  var filename = req.body.filename;
  var ext = filename.split('.').pop();
  var mime = '';
  if (ext === 'c' || ext === 'cpp' || ext === 'cc') {
    mime = 'text/x-c++src';
  } else if (ext === 'py') {
    mime = 'text/x-python';
  }
  var data = {
    stage: 'run',
    mime: mime,
    time_limit: 5,
    filename: filename,
    stdin: '',
    source: content
  };

  docker.run(data, function(d) {
    if (d.stdout) {
      d.stdout = d.stdout.replace(/\n|\r\n|\r/g, '<br>');
      d.stdout = d.stdout.replace(/\s/g, '&nbsp;');
    }
    if (d.stderr) {
      d.stderr = d.stderr.replace(/\n|\r\n|\r/g, '<br>');
      d.stderr = d.stderr.replace(/\s/g, '&nbsp;');
    }
    res.json({
      state: d.state,
      stdout: d.stdout,
      stderr: d.stderr
    });
  });
});


