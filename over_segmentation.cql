:param nameJson => '"name": "David M. Nathan"';
// Which communitites contain "David M. Nathan"
MATCH (p:PUBLICATION)
WHERE p.authors CONTAINS $nameJson
RETURN p.community AS community, count(*) AS size
ORDER BY size DESC;


// Community 0 and 9 have greatest count of "David M. Nathan"

:param C => [0,9];

// Within community edges
MATCH (a:PUBLICATION)-[r:COAUTHOR|COVENUE|COTITLE]-(b:PUBLICATION)
WHERE a.community = 0 AND b.community = 0
  AND a.authors CONTAINS $nameJson AND b.authors CONTAINS $nameJson
RETURN type(r) AS relType,
       count(*) AS edges,
       avg(coalesce(r.weight, r.similarity, 0.0)) AS avgW,
       sum(coalesce(r.weight, r.similarity, 0.0)) AS sumW
ORDER BY sumW DESC;

MATCH (a:PUBLICATION)-[r:COAUTHOR|COVENUE|COTITLE]-(b:PUBLICATION)
WHERE a.community = 9 AND b.community = 9
  AND a.authors CONTAINS $nameJson AND b.authors CONTAINS $nameJson
RETURN type(r) AS relType,
       count(*) AS edges,
       avg(coalesce(r.weight, r.similarity, 0.0)) AS avgW,
       sum(coalesce(r.weight, r.similarity, 0.0)) AS sumW
ORDER BY sumW DESC;


// Cross community edges
MATCH (p1:PUBLICATION)-[r:COAUTHOR|COVENUE|COTITLE]-(p2:PUBLICATION)
WHERE p1.community = 0 AND p2.community = 9
  AND p1.authors CONTAINS $nameJson
  AND p2.authors CONTAINS $nameJson
RETURN type(r) AS relType,
       count(*) AS edges,
       avg(coalesce(r.weight, r.similarity, 0.0)) AS avgW,
       max(coalesce(r.weight, r.similarity, 0.0)) AS maxW,
       sum(coalesce(r.weight, r.similarity, 0.0)) AS sumW
ORDER BY relType;