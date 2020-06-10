var sinon = require ('sinon'),
  chai = require ('chai'),
  sinonChai = require('sinon-chai');

chai.use(sinonChai);

global.expect = chai.expect;

beforeEach(function(){
  global.sinon = sinon.sandbox.create();
});

afterEach(function(){
  global.sinon.restore();
});
