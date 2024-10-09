package ai.flow.common;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.LinkedList;
import java.util.Queue;

public class utils {

    public enum USE_MODEL_RUNNER {
        ONNX, // DOESNT WORK
        SNPE, // Nicki Minaj Model
        TNN, // DOESNT WORK
        THNEED, // Latest
        EXTERNAL_TINYGRAD // DOESNT WORK
    }
    public static boolean F2 = false, NLPModel = false, LAModel = true;
    public static USE_MODEL_RUNNER Runner = USE_MODEL_RUNNER.THNEED;
    public static boolean getBoolEnvVar(String key) {
        String val = System.getenv(key);
        boolean ret = false;
        if (val != null) {
            if (val.equals("1"))
                ret = true;
        }
        return ret;
    }

    public static double secSinceBoot() {
        return System.nanoTime() / 1e9;
    }

    public static double milliSinceBoot() {
        return System.nanoTime() / 1e6;
    }

    public static double nanoSinceBoot() {
        return System.nanoTime();
    }

    public static double numElements(int[] shape){
        double ret = 1;
        for (int i:shape)
            ret *= i;
        return ret;
    }

    public static String readFile(String fileName)
    {
        BufferedReader br = null;
        try
        {
            br = new BufferedReader(new FileReader(fileName));
            StringBuilder sb = new StringBuilder();
            String line = null;
            while (true)
            {
                line = br.readLine();
                if (line == null)
                {
                    break;
                }
                sb.append(line+"\n");
            }
            return sb.toString();
        }
        catch (IOException e)
        {
            e.printStackTrace();
            return "";
        }
        finally
        {
            if (br != null)
            {
                try
                {
                    br.close();
                }
                catch (IOException ex)
                {
                    ex.printStackTrace();
                }
            }
        }
    }
}
