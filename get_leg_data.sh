aws --profile agendawatch dynamodb scan \
  --table-name aw-sites \
  --no-paginate \
  --output json \
  --projection-expression "country, #s, #n, site_type, endpoint" \
  --expression-attribute-names '{"#s":"state", "#n":"name"}' >  data/legistar.json

