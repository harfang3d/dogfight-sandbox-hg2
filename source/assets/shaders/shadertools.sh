float lerp(float a, float b, float w)
{
  return a + w*(b-a);
}

float saturate(float x)
{
  return max(0, min(1, x));
}

float smoothstep(float a, float b, float x)
{
    float t = saturate((x - a)/(b - a));
    return t*t*(3.0 - (2.0*t));
}

float easeIn(float interpolator){
    return interpolator * interpolator;
}

float easeOut(float interpolator){
    return 1. - easeIn(1. - interpolator);
}

float easeInOut(float interpolator){
    float easeInValue = easeIn(interpolator);
    float easeOutValue = easeOut(interpolator);
    return lerp(easeInValue, easeOutValue, interpolator);
}

float rand1dTo1d(float value, float mutator = 0.546){
	float random = fract(sin(value + mutator) * 143758.5453);
	return random;
}


float gradientNoise(float value){
    float previousCellNoise = rand1dTo1d(floor(value));
    float nextCellNoise = rand1dTo1d(ceil(value));
    float interpolator = frac(value);
    interpolator = easeInOut(interpolator);
    return lerp(previousCellNoise, nextCellNoise, interpolator);
}