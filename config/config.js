var path = require('path');
var rootPath = path.normalize(__dirname + '/..');

var config = {
  root: rootPath,
  port: 3000,
  docker: {
    host: '',
    port: 4592,
    runPort: 3000
  }
};

module.exports = config;

