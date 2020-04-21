
  Pod::Spec.new do |s|
    s.name = 'CapacitorFirebaseAnalytics'
    s.version = '0.0.1'
    s.summary = 'Capacitor plugin for ios and Android for using Firebase Analytics'
    s.license = 'MIT'
    s.homepage = 'https://github.com/philmerrell/capacitor-firebase-analytics.git'
    s.author = 'Phil Merrell'
    s.source = { :git => 'https://github.com/philmerrell/capacitor-firebase-analytics.git', :tag => s.version.to_s }
    s.source_files = 'ios/Plugin/Plugin/**/*.{swift,h,m,c,cc,mm,cpp}'
    s.ios.deployment_target  = '11.0'
    s.dependency 'Capacitor'
    s.dependency 'Firebase'
    s.dependency 'Firebase/Core'
    s.static_framework = true
  end