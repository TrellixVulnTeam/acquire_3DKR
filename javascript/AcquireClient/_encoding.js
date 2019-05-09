
/** Standardise the passed datetime into UTC */
function datetime_to_datetime(d)
{
    var date = new Date(d);
    var now_utc =  Date.UTC(date.getUTCFullYear(), date.getUTCMonth(),
                            date.getUTCDate(), date.getUTCHours(),
                            date.getUTCMinutes(), date.getUTCSeconds());

    return new Date(now_utc);
}

/** Convert the passed datetime into a standard formatted string */
function datetime_to_string(d)
{
    d = datetime_to_datetime(d);
    d = d.toISOString();

    if (d.endsWith("Z"))
    {
        d = d.substr(0, d.length-1);
    }

    return d;
}

/** Convert the passed string back into a datetime */
function string_to_datetime(s)
{
    return datetime_to_datetime(Date.parse(s));
}

/** Function to convert from a string back to binary */
function string_to_bytes(s)
{
    return base64js.toByteArray(s);
}

/** Function to convert binary data to a string */
function bytes_to_string(b)
{
    return base64js.fromByteArray(b);
}

/** Convert the passed string to a utf-8 array of bytes */
function string_to_utf8_bytes(s)
{
    return new TextEncoder("utf-8").encode(s);
}

/** Convert the passed array of utf-8 encoded bytes into a string  */
function utf8_bytes_to_string(b)
{
    return new TextDecoder("utf-8").decode(b);
}
