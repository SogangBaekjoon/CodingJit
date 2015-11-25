var codeMirror = null;
var runFilename = null;
var runPath = null;
var runUrl = null;
var spinner = new Spinner().spin();


function spinnerSpin() {
  document.body.appendChild(spinner.el);
}

function spinnerStop() {
  $('body .spinner').remove();
}

$(document).ready(function() {
  $('.logout').click(function() {
    spinnerSpin();
    $.ajax({
      url: '/logout',
      method: 'POST'
    }).done(function() {
      spinnerStop();
      location.href = '/';
    });
  });
});

function resize() {
  var fit = function() {
    $('.CodeMirror').css({
      height: $('.sidebar-2').height()*2/3 - 42
    });
    $('.console-log').css({
      height: $('.sidebar-2').height()/3
    });
  };

  $(document).ready(function() {
    fit();
  });
  $(window).resize(function() {
    fit();
  });
}

function consoleLog(msg, success, err) {
  if (err) {
    $('.console-log').append('<div class="console-err">' + msg + '</div>');
  } else if (success) {
    $('.console-log').append('<div class="console-success">' + msg + '</div>');
  } else {
    $('.console-log').append('<div>' + msg + '</div>');
  }
  $('.console-log').animate({
    scrollTop: $('.console-log')[0].scrollHeight
  }, 'slow');
}

function getRepo() {
  $(document).on('click', '.get-repo', function() {
    var url = $(this).attr('data-url');
    $('.get-repo').removeClass('block');
    $(this).addClass('block');
    spinnerSpin();
    $.ajax({
      url: '/getRepo', 
      method: 'POST',
      data: {
        url: url
      }
    }).done(function(res) {
      spinnerStop();
      $('.file-area').html('');
      res.files.forEach(function(file) {
        console.log(file);
        $('.file-area').append('' + 
          '<div data-path="'+res.path+'" data-filename="'+file+'" class="get-file">'+
          file+
          '</div>');
      });
      $('.file-area').append('' +
        '<div data-path="'+res.path+'" class="make-file" data-toggle="modal" data-target="#create-new-file">'+
        '<i class="fa fa-plus">'+
        '</div>');

      $('.get-file').each(function() {
        var w = $(this).width();
        $(this).css({
          width: w + 45
        });
      });
      runUrl = url;
    });
  });
}

function getFile() {
  $(document).on('click', '.get-file', function() {
    var path = $(this).attr('data-path');
    var filename = $(this).attr('data-filename');
    $('.get-file').removeClass('block');
    $(this).addClass('block');
    spinnerSpin();
    $.ajax({
      url: '/getFile',
      method: 'POST',
      data: {
        path: path,
        filename: filename
      }
    }).done(function(res) {
      var mime = '';
      var ext = filename.split('.').pop();
      if (ext === 'c' || ext === 'cpp' || ext === 'cc') {
        mime = 'text/x-c++src';
      } else if (ext === 'py') {
        mime = 'text/x-python';
      }
      spinnerStop();
      codeMirror.getDoc().setValue(res);
      codeMirror.setOption('mode', mime);
      runFilename = filename;
      runPath = path;
    });
  });
}
function setCodeMirror() {
  var myTextArea = document.getElementById('source');
  console.log(myTextArea);
  codeMirror = CodeMirror.fromTextArea(myTextArea, {
    lineNumbers: true,
    mode: 'text/plain',
    theme: 'lesser-dark'
  });
}

function setRun() {
  $('.run').click(function() {
    if (runFilename) {
    var content = codeMirror.getValue();
    spinnerSpin();
    $.ajax({
      url: '/run',
      method: 'POST',
      data: {
        content: content,
        filename: runFilename
      }
    }).done(function(res) {
      spinnerStop();
      if (typeof res.stdout !== 'undefined' && res.stdout !== '') {
        consoleLog(res.stdout);
      } else {
        consoleLog(res.stderr, 0, 1);
      }
    });
    }
  });
}

function setCommit() {
  $('.send-commit').click(function() {
    if (runFilename) {
      var content = codeMirror.getValue();
      var commitMsg = $('.commit-message').val();
      if (commitMsg !== '' && commitMsg !== null) {
        spinnerSpin();
        $.ajax({
          url: '/commit',
          method: 'POST',
          data: {
            content: content,
            path: runPath,
            filename: runFilename,
            url: runUrl,
            commitMsg: commitMsg
          }
        }).done(function(res) {
          spinnerStop();
          consoleLog(res.stdout, !res.returncode, res.returncode);
          $('#send-commit .close').click();
        });
      } else {
        $('#send-commit .alert-area').text('commit 메세지를 작성해 주세요');
      }

    }
  });
}

function createNewFile() {
  $('.create-new-file').click(function() {
    var filename = $('.create-new-filename').val();
    var path = $('.make-file').attr('data-path');
    runPath = path;
    if (filename) {
      spinnerSpin();
      $.ajax({
        url: '/commit',
        method: 'POST',
        data: {
          content: '',
          path: runPath,
          filename: filename,
          url: runUrl,
          commitMsg: 'add ' + filename
        }
      }).done(function(res) {
        spinnerStop();
        consoleLog(res.stdout, !res.returncode, res.returncode);
        if (!res.returncode) {
          $('.make-file').wrap('<div>');
          $('.make-file').parent().prepend(''+
          '<div data-path="'+runPath+'" data-filename="'+filename+'" class="get-file">'+
          filename+
          '</div>');
          $('.make-file').siblings('.get-file').click();
          $('.make-file').unwrap();
        }
      });
      $('#create-new-file .close').click();
    } else {
      $('#create-new-file .alert-area').text('파일 이름을 작성해주세요');
    }
  });
}

function makeRepo() {
  $('.make-repo').click(function() {
    var repoName = $('#new-repo .repo-name').val();
    var repoDesc = $('#new-repo .repo-description').val();

    if (repoName !== '') {
      spinnerSpin();
      $.ajax({
        url: '/newRepo',
        method: 'POST',
        data: {
          repoName: repoName,
          repoDesc: repoDesc
        }
      }).done(function(res) {
        spinnerStop();
        $('.plus-repo').wrap('<div>');
        $('.plus-repo').parent().prepend(''+
          '<div data-url="'+res.url+'" class="get-repo">'+
          repoName+
          '</div>');
        $('.plus-repo').siblings('.get-repo').click();
        $('.plus-repo').unwrap();
        $('#new-repo .close').click();
      });
    } else {
      $('#new-repo .alert-area').text('Repository 이름을 작성해 주세요');
    }
  });
}
