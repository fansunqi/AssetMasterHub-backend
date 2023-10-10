coverage run --source CS_Company_backend,User,Asset,utils -m pytest --junit-xml=xunit-reports/xunit-result.xml
ret=$?
coverage xml -o coverage-reports/coverage.xml
coverage report
exit $ret