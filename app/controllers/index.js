var express = require('express');
var router = express.Router();

module.exports = function(app) {
  app.use('/', router);
};

router.get('/', function(req, res, next) {
  if (req.session.username) {
    return res.redirect('/getRepoList');
  } else {
    res.render('login', {
      flash: req.flash('login')
    });
  }
});
