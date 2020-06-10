'use strict';

var proxyquire = require('proxyquire'),
    sinon = require('sinon');

describe('Logging Middleware Tests', function() {

  var loggingMiddleware,
      loggerSpy;

  beforeEach(function() {
    var loggerMock = {
      info: function() {}
    };
    loggerSpy = sinon.spy(loggerMock, 'info');

    var onHeadersMock = function(res, cb) {
      cb();
    };

    var LoggingMiddleware = proxyquire('../../lib/logging', {
      'on-headers': onHeadersMock
    });
    loggingMiddleware = new LoggingMiddleware(loggerMock);
  });

  it('should log the request and response', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function() {
        return null;
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        'Request from %s: %s %s',
        '10.128.201.134',
        'GET',
        '/test?jwt=xxx']);
      expect(loggerSpy.getCall(1).args[0]).to.be.equal('Response with status %d in %d ms.');
      expect(loggerSpy.getCall(1).args[1]).to.be.equal(200);
    });
  });

  it('should log the request and response with location header', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function() {
        return null;
      }
    };
    var res = {
      statusCode: 302,
      get: function(headerName) {
        if (headerName === 'location') {
          return 'http://localhost:9000/location';
        } else {
          return null;
        }
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        'Request from %s: %s %s',
        '10.128.201.134',
        'GET',
        '/test?jwt=xxx']);
      expect(loggerSpy.getCall(1).args[0]).to.be.equal('Response with status %d in %d ms. Location: %s');
      expect(loggerSpy.getCall(1).args[1]).to.be.equal(302);
      expect(loggerSpy.getCall(1).args[3]).to.be.equal('http://localhost:9000/location');
    });
  });

  it('should log the request and response with client IP from XFF header', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function(name) {
        if (name === 'x-forwarded-for') {
          return '1.1.1.1, 10.128.201.200';
        } else {
          return null;
        }
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        'Request from %s: %s %s',
        '10.128.201.200',
        'GET',
        '/test?jwt=xxx']);
      expect(loggerSpy.getCall(1).args[0]).to.be.equal('Response with status %d in %d ms.');
      expect(loggerSpy.getCall(1).args[1]).to.be.equal(200);
    });
  });

  it('should log the request and response with client IP from request if invalid XFF header', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function(name) {
        if (name === 'x-forwarded-for') {
          return '1.1.1.1, 10.128.201.200, ';
        } else {
          return null;
        }
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        'Request from %s: %s %s',
        '10.128.201.134',
        'GET',
        '/test?jwt=xxx']);
      expect(loggerSpy.getCall(1).args[0]).to.be.equal('Response with status %d in %d ms.');
      expect(loggerSpy.getCall(1).args[1]).to.be.equal(200);
    });
  });

});

describe('Logging Middleware Tests with params policy', function() {

  var loggingMiddleware,
      loggerSpy;

  beforeEach(function() {
    var loggerMock = {
      info: function() {}
    };
    loggerSpy = sinon.spy(loggerMock, 'info');

    var onHeadersMock = function(res, cb) {
      cb();
    };

    var LoggingMiddleware = proxyquire('../../lib/logging', {
      'on-headers': onHeadersMock
    });
    loggingMiddleware = new LoggingMiddleware(loggerMock, {policy: 'params'});
  });

  it('should log the request and response', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function() {
        return null;
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        {
          requestClientIp: '10.128.201.134',
          requestMethod: 'GET',
          requestUrl: '/test?jwt=xxx'
        },
        'Request: %s %s',
        'GET',
        '/test?jwt=xxx'
      ]);
      expect(loggerSpy.getCall(1).args[0].responseStatusCode).to.be.equal(200);
      expect(loggerSpy.getCall(1).args[0].responseLocation).not.to.be.defined;
      expect(loggerSpy.getCall(1).args[1]).to.be.equal('Response with status %d');
      expect(loggerSpy.getCall(1).args[2]).to.be.equal(200);
    });
  });

  it('should log the request and response with location header', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function() {
        return null;
      }
    };
    var res = {
      statusCode: 302,
      get: function(headerName) {
        if (headerName === 'location') {
          return 'http://localhost:9000/location';
        } else {
          return null;
        }
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        {
          requestClientIp: '10.128.201.134',
          requestMethod: 'GET',
          requestUrl: '/test?jwt=xxx'
        },
        'Request: %s %s',
        'GET',
        '/test?jwt=xxx'
      ]);
      expect(loggerSpy.getCall(1).args[0].responseStatusCode).to.be.equal(302);
      expect(loggerSpy.getCall(1).args[0].responseLocation).to.be.equal('http://localhost:9000/location');
      expect(loggerSpy.getCall(1).args[1]).to.be.equal('Response with status %d');
      expect(loggerSpy.getCall(1).args[2]).to.be.equal(302);
    });
  });

  it('should log the request and response with client IP from XFF header', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function(name) {
        if (name === 'x-forwarded-for') {
          return '1.1.1.1, 10.128.201.200';
        } else {
          return null;
        }
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        {
          requestClientIp: '10.128.201.200',
          requestMethod: 'GET',
          requestUrl: '/test?jwt=xxx'
        },
        'Request: %s %s',
        'GET',
        '/test?jwt=xxx'
      ]);
      expect(loggerSpy.getCall(1).args[0].responseStatusCode).to.be.equal(200);
      expect(loggerSpy.getCall(1).args[0].responseLocation).not.to.be.defined;
      expect(loggerSpy.getCall(1).args[1]).to.be.equal('Response with status %d');
      expect(loggerSpy.getCall(1).args[2]).to.be.equal(200);
    });
  });

  it('should log the request and response with client IP from request if invalid XFF header', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function(name) {
        if (name === 'x-forwarded-for') {
          return '1.1.1.1, 10.128.201.200, ';
        } else {
          return null;
        }
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        {
          requestClientIp: '10.128.201.134',
          requestMethod: 'GET',
          requestUrl: '/test?jwt=xxx'
        },
        'Request: %s %s',
        'GET',
        '/test?jwt=xxx'
      ]);
      expect(loggerSpy.getCall(1).args[0].responseStatusCode).to.be.equal(200);
      expect(loggerSpy.getCall(1).args[0].responseLocation).not.to.be.defined;
      expect(loggerSpy.getCall(1).args[1]).to.be.equal('Response with status %d');
      expect(loggerSpy.getCall(1).args[2]).to.be.equal(200);
    });
  });

});

describe('Logging Middleware Tests with blacklist', function() {

  var loggingMiddleware,
      loggerSpy;

  beforeEach(function() {
    var loggerMock = {
      info: function() {}
    };
    loggerSpy = sinon.spy(loggerMock, 'info');

    var onHeadersMock = function(res, cb) {
      cb();
    };

    var LoggingMiddleware = proxyquire('../../lib/logging', {
      'on-headers': onHeadersMock
    });
    loggingMiddleware = new LoggingMiddleware(loggerMock, {blacklist: ['/blacklist']});
  });

  it('should log the request and response', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/test?jwt=xxx',
      get: function() {
        return null;
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.calledTwice).to.be.true;
      expect(loggerSpy.getCall(0).args).to.be.deep.equal([
        'Request from %s: %s %s',
        '10.128.201.134',
        'GET',
        '/test?jwt=xxx']);
      expect(loggerSpy.getCall(1).args[0]).to.be.equal('Response with status %d in %d ms.');
      expect(loggerSpy.getCall(1).args[1]).to.be.equal(200);
    });
  });

  it('should not log anything when the url path is in the blacklist', function() {
    var req = {
      method: 'GET',
      ip: '10.128.201.134',
      originalUrl: '/blacklist/test?jwt=xxx',
      get: function() {
        return null;
      }
    };
    var res = {
      statusCode: 200,
      get: function() {
        return null;
      }
    };

    loggingMiddleware(req, res, function() {
      expect(loggerSpy.called).to.be.false;
    });
  });

});
