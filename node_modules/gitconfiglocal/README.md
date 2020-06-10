
[![Build Status](https://travis-ci.org/soldair/node-gitconfiglocal.svg?branch=master)](https://travis-ci.org/soldair/node-gitconfiglocal)

gitconfiglocal
==============

parse the `.git/config` file into a useful data structure


example
=======

- search config in $GIT_DIR (.git by default)
```js
var gitconfig = require('gitconfiglocal');

gitconfig('./',function(err,config){
  console.log(config);
  /* prints:
  { core:
     { repositoryformatversion: '0',
       filemode: true,
       bare: false,
       logallrefupdates: true },
    remote:
     { origin:
        { url: 'git@github.com:soldair/node-gitconfiglocal.git',
          fetch: '+refs/heads/*:refs/remotes/origin/*' } } }
  */
});

```

- specify $GIT_DIR via options:
```js
gitconfig('./', { gitDir: 'path/to/gitdir' }, cb);

```
