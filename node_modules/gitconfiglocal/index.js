//@ts-check
var fs = require('fs');
var ini = require('ini');
var path = require('path');


module.exports = function(dir,options,cb){
  if (typeof options === 'function') {
    cb = options;
    options = {};
  }
  findGit(dir,options,function(config) {
    if(!config) return cb(new Error('no gitconfig to be found at '+dir))
    fs.readFile(config,function(err,data){
      if(err) return cb(err);
      try{
       var formatted = format(ini.parse(data.toString()));
      } catch (e){
       return cb(e);
      }
      cb(false,formatted);
    })
  })
}

function format(data){
  var out = {};
  Object.keys(data).forEach(function(k){
    if(k.indexOf('"')> -1) {
      var parts = k.split('"');
      var parentKey = parts.shift().trim();
      var childKey = parts.shift().trim();
      if(!out[parentKey]) out[parentKey] = {};
      out[parentKey][childKey] = data[k];
    } else {
      out[k] = merge(out[k],data[k])
      // cant start using these without bumping the major
      //out[k] = {...out[k], ...data[k]};
    }
  });
  return out;
}

function findGit(dir,options,cb){
  var folder = path.resolve(dir, options.gitDir || process.env.GIT_DIR || '.git', 'config');
  fs.exists(folder,function(exists) {
    if(exists) return cb(folder);
    if(dir === path.resolve(dir, '..')) return cb(false);
    findGit(path.resolve(dir, '..'), options, cb);
  });
}

function merge(){
  var a = {}
  for(var i=arguments.length;i>=0;--i){
    Object.keys(arguments[i]||{}).forEach((k)=>{
      a[k] = arguments[i][k]
    })
  }
  return a;
}
