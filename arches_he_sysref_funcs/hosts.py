import re
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(
        re.sub(r"_", r"-", r"arches_he_sysref_funcs"),
        "arches_he_sysref_funcs.urls",
        name="arches_he_sysref_funcs",
    ),
)
