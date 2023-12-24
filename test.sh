#/bin/bash

py="src/wbx_admin_utils/__main__.py"

python3 $py co list-user-sent-msgs bc@4bfzj5.onmicrosoft.com
echo "--------"

python3 $py -T co list-user-sent-msgs bc@4bfzj5.onmicrosoft.com '{"max":5}'
cho "--------"

python3 $py -c "/tmp/msgs.csv" co list-user-sent-msgs bc@4bfzj5.onmicrosoft.com '{"max":5}'
cat "/tmp/msgs.csv"
echo "--------"

