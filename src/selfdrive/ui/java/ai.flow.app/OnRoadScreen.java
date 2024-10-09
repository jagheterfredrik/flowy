package ai.flow.app;

import ai.flow.app.helpers.GifDecoder;
import ai.flow.app.helpers.Utils;
import ai.flow.common.ParamsInterface;
import ai.flow.common.Path;
import ai.flow.common.transformations.Camera;
import ai.flow.common.utils;
import ai.flow.definitions.CarDefinitions.CarControl.HUDControl.AudibleAlert;
import ai.flow.definitions.Definitions;
import ai.flow.modeld.CommonModelF3;
import ai.flow.modeld.ModelExecutor;
import ai.flow.modeld.ModelExecutorF3;
import ai.flow.modeld.ParsedOutputs;
import ai.flow.modeld.Preprocess;
import ai.flow.modeld.messages.MsgModelDataV2;
import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.InputMultiplexer;
import com.badlogic.gdx.ScreenAdapter;
import com.badlogic.gdx.audio.Sound;
import com.badlogic.gdx.graphics.*;
import com.badlogic.gdx.graphics.g2d.Animation;
import com.badlogic.gdx.graphics.g2d.SpriteBatch;
import com.badlogic.gdx.graphics.g2d.TextureRegion;
import com.badlogic.gdx.graphics.glutils.ShapeRenderer;
import com.badlogic.gdx.scenes.scene2d.InputEvent;
import com.badlogic.gdx.scenes.scene2d.Stage;
import com.badlogic.gdx.scenes.scene2d.ui.*;
import com.badlogic.gdx.scenes.scene2d.utils.ClickListener;
import com.badlogic.gdx.utils.Align;
import com.badlogic.gdx.utils.viewport.FillViewport;
import com.badlogic.gdx.utils.viewport.FitViewport;
import com.badlogic.gdx.utils.viewport.ScreenViewport;
import com.badlogic.gdx.utils.viewport.StretchViewport;

import messaging.ZMQPubHandler;
import messaging.ZMQSubHandler;
import org.apache.commons.lang3.ArrayUtils;
import org.capnproto.PrimitiveList;
import org.nd4j.linalg.api.memory.MemoryWorkspace;
import org.nd4j.linalg.api.memory.conf.WorkspaceConfiguration;
import org.nd4j.linalg.api.memory.enums.AllocationPolicy;
import org.nd4j.linalg.api.memory.enums.LearningPolicy;
import org.nd4j.linalg.api.ndarray.INDArray;
import org.nd4j.linalg.factory.Nd4j;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

import static ai.flow.app.helpers.Utils.getImageButton;
import static ai.flow.app.helpers.Utils.loadTextureMipMap;
import static ai.flow.sensor.messages.MsgFrameBuffer.updateImageBuffer;


public class OnRoadScreen extends ScreenAdapter {
    // avoid GC triggers.
    static final String VERSION = "73";
    final WorkspaceConfiguration wsConfig = WorkspaceConfiguration.builder()
            .policyAllocation(AllocationPolicy.STRICT)
            .policyLearning(LearningPolicy.FIRST_LOOP)
            .build();
    FlowUI appContext;
    ParamsInterface params = ParamsInterface.getInstance();
    // For camera frame receiving
    Pixmap pixelMap;
    Texture texture;
    //batch
    SpriteBatch batch;
    // ui
    Stage stageFill, stageUI, stageAlert, stageSettings;
    OrthographicCamera cameraModel, cameraAlertBox;
    Image texImage;
    int defaultDrawLength = 30;
    int drawResolution = 1;
    float fadeStrength = 0.03f;
    float minZ = 0.2f;
    float minLeadProb = 0.333f;
    float leadDrawScale = 6f;
    float borderWidth = 30;
    float expandedBorderWidth = 600;
    int defaultImageWidth = Camera.frameSize[0];
    int defaultImageHeight = Camera.frameSize[1];
    // draw array buffers
    INDArray[] path, lane0, lane1, lane2, lane3;
    INDArray[] edge0, edge1;
    INDArray lead1s, lead2s, lead3s;
    INDArray augmentRot = Nd4j.zeros(1, 3);
    INDArray augmentTrans = Nd4j.zeros(1, 3);
    int[] colorPath = {0, 162, 255};
    int[] colorEdges = {255, 0, 255};
    int[] colorLead = {196, 196, 196};
    int[] colorBorder;
    float[] colorSettingsBar = {46f/255, 46f/255, 46f/255};
    // comm params
    boolean modelAlive, controlsAlive;
    ZMQSubHandler sh;
    ZMQPubHandler ph;
    Definitions.ControlsState.Reader controlState;
    String modelTopic = "modelV2";
    String cameraTopic = "wideRoadCameraState";
    String cameraBufferTopic = "wideRoadCameraBuffer";
    String calibrationTopic = "liveCalibration";
    String carStateTopic = "carState";
    String controlsStateTopic = "controlsState";
    String deviceStateTopic = "deviceState";
    String Line1 = "Empty", Line2 = "Empty";
    public static int CamExposure, currentExposureIndex = 0;

    Label velocityLabel, velocityUnitLabel, alertText1, alertText2, maxCruiseSpeedLabel, dateLabel, vesrionLabel;
    Table velocityTable, maxCruiseTable, alertTable, infoTable, offRoadTable, rootTable, offRoadRootTable;
    Stack statusLabelTemp, statusLabelCan, statusLabelOnline, maxCruise;
    ScrollPane notificationScrollPane;
    ImageButton settingsButton;
    ParsedOutputs parsed = new ParsedOutputs();
    int canErrCount = 0;
    int canErrCountPrev = 0;
    int canMisses = 0;
    float uiWidth = 1280;
    float uiHeight = 640;
    int notificationWidth = 950;
    float settingsBarWidth;
    boolean cameraMatrixUpdated = false;
    boolean isMetric;
    ByteBuffer imgBuffer;
    NV12Renderer nv12Renderer;
    Definitions.FrameBuffer.Reader msgframeBuffer;
    Definitions.FrameData.Reader msgframeData;
    Animation<TextureRegion> animationNight, animationNoon, animationSunset;
    Map<String, String> offroadNotifications = new HashMap<String, String>() {{
        put("Offroad_TemperatureTooHigh", "Device temperature too high. System won't start.");
        put("Offroad_ConnectivityNeeded", "Connect to internet to check for updates. flowpilot won't automatically start until it connects to internet to check for updates.");
        put("Offroad_InvalidTime", "Invalid date and time settings, system won't start until date time are set correctly.");
    }};
    Map<AudibleAlert, Sound> soundAlerts;
    double elapsed;

    long[] LastDebugMessageTime = new long[2];

    public boolean NoDebugMessagesWarning() {
        return System.currentTimeMillis() - Math.min(LastDebugMessageTime[0], LastDebugMessageTime[1]) > 500;
    }

    public void PrepareDebugReader() {
        LastDebugMessageTime[0] = System.currentTimeMillis();
        LastDebugMessageTime[1] = System.currentTimeMillis();
        Thread thread = new Thread(() -> {
            try {
                InetAddress localhost = InetAddress.getByName("localhost");
                DatagramSocket s      = new DatagramSocket(9000);
                byte[] buf = new byte[512];
                while(true) {
                    DatagramPacket p = new DatagramPacket(buf, buf.length);
                    s.receive(p);
                    String debugLine = new String(buf, 0, p.getLength());
                    if (debugLine.startsWith("0")) {
                        Line1 = debugLine.replace('\n', ' ').substring(1);
                        LastDebugMessageTime[0] = System.currentTimeMillis();
                    } else {
                        Line2 = debugLine.replace('\n', ' ');
                        LastDebugMessageTime[1] = System.currentTimeMillis();
                    }
                }
            } catch (Exception e) {}
        });
        thread.setDaemon(true);
        thread.setPriority(Thread.NORM_PRIORITY - 1);
        thread.start();
    }

    public enum UIStatus {
        STATUS_DISENGAGED,
        STATUS_OVERRIDE,
        STATUS_ENGAGED,
        STATUS_WARNING,
        STATUS_ALERT,
    }
    UIStatus status= UIStatus.STATUS_DISENGAGED;
    Map<UIStatus, int[]> statusColors  = new HashMap<UIStatus, int[]>() {{
        put(UIStatus.STATUS_DISENGAGED, new int[] {23, 51, 73});
        put(UIStatus.STATUS_OVERRIDE, new int[] {145, 155, 149});
        put(UIStatus.STATUS_ENGAGED, new int[] {43, 143, 40});
        put(UIStatus.STATUS_WARNING, new int[] {222, 15, 15});
        put(UIStatus.STATUS_ALERT, new int[] {222, 15, 15});
    }};
    AudibleAlert[] repeatingAlerts = {AudibleAlert.PROMPT_DISTRACTED, AudibleAlert.PROMPT_REPEAT,
            AudibleAlert.WARNING_IMMEDIATE, AudibleAlert.WARNING_SOFT};
    AudibleAlert currentAudibleAlert;

    public static class StatusColors{
        public static final float[] colorStatusGood = {255/255f, 255/255f, 255/255f};
        public static final float[] colorStatusCritical = {201/255f, 34/255f, 49/255f};
        public static final float[] colorStatusWarn = {218/255f, 202/255f, 37/255f};
    }

    public void updateAugmentVectors(Definitions.LiveCalibrationData.Reader liveCalib){
        PrimitiveList.Float.Reader rpy = liveCalib.getRpyCalib();
        for (int i=0; i<3; i++)
            augmentRot.put(0, i, rpy.get(i));
    }

    public Stack getStatusLabel(String text){
        Image borderTexture = new Image(new Texture(Gdx.files.absolute(Path.internal("selfdrive/assets/icons/rounded-border.png"))));
        Image statusTexture = new Image(loadTextureMipMap("selfdrive/assets/icons/status_label.png"));
        Label textLabel = new Label(text, appContext.skin, "default-font-bold", "white");
        textLabel.setAlignment(Align.center);
        return new Stack(borderTexture, statusTexture, textLabel);
    }

    public void addNotification(String text){
        Image backgroundTexture = new Image(Utils.createRoundedRectangle(notificationWidth, 50, 2, new Color(224/255f, 18/255f, 18/255f, 0.7f)));
        // green 50, 168, 52
        Label textLabel = new Label(text, appContext.skin, "default-font-20", "white");
        textLabel.setAlignment(Align.left);
        textLabel.setWrap(true);
        Container container = new Container(textLabel);
        container.left().pad(10).width(900);
        offRoadTable.add(new Stack(backgroundTexture, container)).padLeft(10).padRight(10).padTop(10);
        offRoadTable.row();
    }

    public void updateOffroadNotifications(){
        clearNotifications();
        for (String notification : offroadNotifications.keySet()){
            if (params.exists(notification)){
                addNotification(offroadNotifications.get(notification));
            }
        }
    }

    public void clearNotifications(){
        offRoadTable.clear();
    }

    public void updateStatusLabel(Stack statusLabel, float[] color){
        statusLabel.getChild(1).setColor(color[0], color[1], color[2], 0.8f);
    }

    float updateTempTimer;
    NumberFormat formatter = new DecimalFormat("0.0");
    String tempStr = "--c", IPstring = "No Internet";
    public static int CamSelected = 0;

    public void UpdateIP() {
        try {
            Enumeration networkInterfaces = NetworkInterface.getNetworkInterfaces();  // gets All networkInterfaces of your device
            while (networkInterfaces.hasMoreElements()) {
                NetworkInterface inet = (NetworkInterface) networkInterfaces.nextElement();
                Enumeration address = inet.getInetAddresses();
                while (address.hasMoreElements()) {
                    InetAddress inetAddress = (InetAddress) address.nextElement();
                    if (inetAddress.isSiteLocalAddress()) {
                        IPstring = inetAddress.getHostAddress();
                        return;
                    }
                }
            }
        } catch (Exception e) {
            // Handle Exception
        }
        IPstring = "No Internet";
    }

    public void UpdateTemps() {
        java.nio.file.Path cpuPath = Paths.get("/sys/devices/virtual/thermal/thermal_zone0/temp");
        java.nio.file.Path gpuPath = Paths.get("/sys/devices/virtual/thermal/thermal_zone10/temp");
        float CPUTemp = 0f, GPUTemp = 0f;
        try {
            CPUTemp = Float.parseFloat(Files.readAllLines(cpuPath).get(0)) / 1000f;
            GPUTemp = Float.parseFloat(Files.readAllLines(gpuPath).get(0)) / 1000f;
        } catch (Exception e) {}
        float MaxTemp = Math.max(CPUTemp, GPUTemp);
        tempStr = formatter.format(MaxTemp) + "c";
    }

    public void updateDeviceState(){
        Definitions.DeviceState.Reader deviceState = sh.recv(deviceStateTopic).getDeviceState();
        Definitions.DeviceState.ThermalStatus thermalStatus = deviceState.getThermalStatus();
        if (thermalStatus == Definitions.DeviceState.ThermalStatus.GREEN)
            updateStatusLabel(statusLabelTemp, "TEMP\nGOOD", StatusColors.colorStatusGood);
        else if (thermalStatus == Definitions.DeviceState.ThermalStatus.YELLOW)
            updateStatusLabel(statusLabelTemp, "TEMP\nHIGH", StatusColors.colorStatusWarn);
        else if (thermalStatus == Definitions.DeviceState.ThermalStatus.RED)
            updateStatusLabel(statusLabelTemp, "TEMP\nCRITICAL", StatusColors.colorStatusCritical);
        else if (thermalStatus == Definitions.DeviceState.ThermalStatus.DANGER)
            updateStatusLabel(statusLabelTemp, "TEMP\nDANGER", StatusColors.colorStatusCritical);
    }

    public void updateStatusLabel(Stack statusLabel, String text, float[] color){
        statusLabel.getChild(1).setColor(color[0], color[1], color[2], 0.8f);
        Label label = (Label)statusLabel.getChild(2);
        label.setText(text);
    }

    public Stack getMaxVelocityLabel(){
        Image bg = new Image(new Texture(Gdx.files.absolute(Path.internal("selfdrive/assets/icons/max_cruise.png"))));
        bg.setColor(0.25f, 0.25f, 0.25f, 0.8f);
        Table table = new Table();
        Label maxLabel = new Label("MAX", appContext.skin, "default-font", "white");
        maxLabel.setColor(0.8f, 0.8f, 0.8f, 1f);
        maxCruiseSpeedLabel = new Label("N/A", appContext.skin, "default-font-bold-med", "white");
        maxLabel.setAlignment(Align.top);
        maxCruiseSpeedLabel.setFontScale(1.4f, 1.4f);
        maxCruiseSpeedLabel.setAlignment(Align.bottom);
        table.add(maxLabel).padTop(2);
        table.row();
        table.add(maxCruiseSpeedLabel).padBottom(2);
        return new Stack(bg, table);
    }

    @SuppressWarnings("NewApi")
    public OnRoadScreen(FlowUI appContext) {
        this.appContext = appContext;

        PrepareDebugReader();

        soundAlerts = new HashMap<AudibleAlert, Sound>() {{
            put(AudibleAlert.ENGAGE, appContext.engageSound);
            put(AudibleAlert.DISENGAGE, appContext.disengageSound);
            put(AudibleAlert.REFUSE, appContext.refuseSound);
            put(AudibleAlert.PROMPT, appContext.promptSound);
            put(AudibleAlert.PROMPT_REPEAT, appContext.promptSound);
            put(AudibleAlert.PROMPT_DISTRACTED, appContext.promptDistractedSound);
            put(AudibleAlert.WARNING_SOFT, appContext.warningSoft);
            put(AudibleAlert.WARNING_IMMEDIATE, appContext.warningImmediate);
        }};

        batch = new SpriteBatch();
        pixelMap = new Pixmap(defaultImageWidth, defaultImageHeight, Pixmap.Format.RGB888);
        pixelMap.setBlending(Pixmap.Blending.None);
        texture = new Texture(pixelMap);
        settingsBarWidth = uiWidth / 3f * Gdx.graphics.getHeight() / Gdx.graphics.getWidth();

        rootTable = new Table();
        rootTable.setFillParent(true);
        rootTable.align(Align.left);

        infoTable = new Table();
        Utils.setTableColor(infoTable, colorSettingsBar[0], colorSettingsBar[1], colorSettingsBar[2], 1);

        rootTable.add(infoTable).expandY();

        velocityTable = new Table();
        velocityTable.setFillParent(true);
        velocityTable.align(Align.top);
        velocityTable.padTop(20);

        maxCruiseTable = new Table();
        maxCruiseTable.setFillParent(true);
        maxCruiseTable.align(Align.topLeft);
        maxCruiseTable.padTop(100);

        alertTable = new Table();
        alertTable.setFillParent(true);
        alertTable.align(Align.bottom);
        alertTable.padBottom(100);

        offRoadRootTable = new Table();
        offRoadRootTable.setFillParent(true);
        offRoadRootTable.align(Align.left);

        offRoadTable = new Table();
        offRoadTable.setBackground(Utils.createRoundedRectangle(notificationWidth, 550, 10, new Color(0.18f, 0.18f, 0.18f, 0.7f)));

        notificationScrollPane = new ScrollPane(offRoadTable);
        notificationScrollPane.setSmoothScrolling(true);
        offRoadTable.align(Align.top);

        DateTimeFormatter f = DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).withLocale(Locale.US);
        dateLabel = new Label(LocalDateTime.now().format(f),  appContext.skin, "default-font-30", "white");

        String version = params.exists("Version") ? "flowpilot v" + params.getString("Version") : "";
        vesrionLabel = new Label(version,  appContext.skin, "default-font-30", "white");
        offRoadRootTable.add(dateLabel).align(Align.topLeft).padTop(15);
        offRoadRootTable.add(vesrionLabel).padTop(15).align(Align.topRight);
        offRoadRootTable.row();
        offRoadRootTable.add(notificationScrollPane).colspan(2).align(Align.left).padTop(10);

        rootTable.add(offRoadRootTable).padLeft(20);

        cameraModel = new OrthographicCamera(defaultImageWidth, defaultImageHeight);
        cameraModel.setToOrtho(true, defaultImageWidth, defaultImageHeight);
        cameraModel.update();

        stageSettings = new Stage(new StretchViewport(uiWidth, uiHeight));

        cameraAlertBox = new OrthographicCamera(uiWidth, uiHeight);
        cameraAlertBox.setToOrtho(false, uiWidth, uiHeight);
        cameraAlertBox.translate(-settingsBarWidth, 0, 0);
        cameraAlertBox.update();

        // used to maintain aspect ratio of stream
        stageFill = new Stage(new FillViewport(defaultImageWidth, defaultImageHeight));
        // used to draw UI components with respect to screen dimensions.
        stageUI = new Stage(new FitViewport(uiWidth, uiHeight));
        // used to draw alert messages.
        stageAlert = new Stage(new ScreenViewport());

        velocityLabel = new Label("", appContext.skin, "default-font-bold-large", "white");
        velocityLabel.setColor(0.5f, 1f, 0.5f, 1f);
        velocityUnitLabel = new Label("", appContext.skin, "default-font", "white");
        velocityUnitLabel.setColor(0.5f, 1f, 0.5f, 1f);
        isMetric = params.existsAndCompare("IsMetric", true);

        alertText1 = new Label("Flowpilot Unavailable", appContext.skin, "default-font-bold-med", "white");
        alertText2 = new Label("Waiting for controls to start", appContext.skin, "default-font", "white");

        texImage = new Image(texture);

        maxCruise = getMaxVelocityLabel();
        maxCruiseTable.add(maxCruise).align(Align.left).padLeft(30);

        velocityTable.add(velocityLabel).align(Align.top);
        velocityTable.row();
        velocityTable.add(velocityUnitLabel).fillY().align(Align.top);

        alertTable.add(alertText1);
        alertTable.row();
        alertTable.add(alertText2).pad(15);

        settingsButton = getImageButton("selfdrive/assets/icons/button_settings.png");
        settingsButton.addListener(new ClickListener() {
            @Override
            public void clicked(InputEvent event, float x, float y) {
                appContext.setScreen(appContext.settingsScreen);
            }
        });
        settingsButton.setColor(1, 1, 1, 0.6f);
        infoTable.add(settingsButton).align(Align.top).height(uiHeight/9f).width(settingsBarWidth).padTop(50);
        infoTable.row();
        statusLabelTemp = getStatusLabel("TEMP\nGOOD");
        updateStatusLabel(statusLabelTemp, StatusColors.colorStatusGood);
        infoTable.add(statusLabelTemp).align(Align.top).height(uiHeight/8f).width(settingsBarWidth*0.8f).padTop(60);
        infoTable.row();
        statusLabelCan = getStatusLabel("CAN\nOFFLINE");
        updateStatusLabel(statusLabelCan, StatusColors.colorStatusCritical);
        infoTable.add(statusLabelCan).align(Align.top).height(uiHeight/8f).width(settingsBarWidth*0.8f).padTop(20);
        infoTable.row();
        statusLabelOnline = getStatusLabel("FLICKS\nOFFLINE");
        updateStatusLabel(statusLabelOnline, StatusColors.colorStatusWarn);
        infoTable.add(statusLabelOnline).align(Align.top).height(uiHeight/8f).width(settingsBarWidth*0.8f).padTop(20);
        infoTable.row();
        Image logoTexture = new Image(loadTextureMipMap("selfdrive/assets/icons/circle-white.png"));
        logoTexture.setColor(1, 215/255f, 0, 0.6f);
        infoTable.add(logoTexture).align(Align.top).size(110).padTop(35).padBottom(40);

        stageFill.addActor(texImage);
        stageUI.addActor(velocityTable);
        stageUI.addActor(maxCruiseTable);
        stageUI.addActor(alertTable);
        stageSettings.addActor(rootTable);

        velocityTable.moveBy(settingsBarWidth/2f, 0); // TODO is this really correct ?
        alertTable.moveBy(settingsBarWidth/2f, 0);
        maxCruiseTable.moveBy(settingsBarWidth, 0);

        texImage.addListener(new ClickListener() {
            @Override
            public void clicked(InputEvent event, float x, float y) {
                if (!appContext.isOnRoad)
                    return;
                setInfoTable(!infoTable.isVisible());
            }
        });

        animationNoon = GifDecoder.loadGIFAnimation(Animation.PlayMode.LOOP, Gdx.files.absolute(Path.internal("selfdrive/assets/gifs/noon.gif")).read());
        animationSunset = GifDecoder.loadGIFAnimation(Animation.PlayMode.LOOP, Gdx.files.absolute(Path.internal("selfdrive/assets/gifs/sunset.gif")).read());
        animationNight = GifDecoder.loadGIFAnimation(Animation.PlayMode.LOOP, Gdx.files.absolute(Path.internal("selfdrive/assets/gifs/night.gif")).read());

        sh = new ZMQSubHandler(true);
        sh.createSubscribers(Arrays.asList("lateralPlan", cameraTopic, cameraBufferTopic, deviceStateTopic, calibrationTopic, carStateTopic, controlsStateTopic, modelTopic, "roadCameraBuffer", "roadCameraState"));
    }

    public static boolean HideInfoTable;

    public void setInfoTable(boolean visible) {
        infoTable.setVisible(visible);
        if (infoTable.isVisible()) {
            cameraAlertBox.translate(-settingsBarWidth, 0, 0);
            velocityTable.moveBy(settingsBarWidth/2f, 0);
            alertTable.moveBy(settingsBarWidth/2f, 0);
            maxCruiseTable.moveBy(settingsBarWidth, 0);
        }
        else {
            cameraAlertBox.translate(settingsBarWidth, 0, 0);
            velocityTable.moveBy(-settingsBarWidth/2f, 0);
            alertTable.moveBy(-settingsBarWidth/2f, 0);
            maxCruiseTable.moveBy(-settingsBarWidth, 0);
        }
        cameraAlertBox.update();
    }

    public Animation<TextureRegion> getCurrentAnimation(){
        @SuppressWarnings("NewApi") int hour = LocalDateTime.now().getHour();
        if (hour >= 20 || hour < 7)
            return  animationNight;
        else if (hour < 19)
            return animationNoon;
        else
            return animationSunset;
    }

    public void setDefaultAlert(){
        alertText1.setText("Flowpilot Unavailable");
        alertText2.setText("Waiting for controls to start");
    }

    @Override
    public void show() {
        InputMultiplexer inputMultiplexer = new InputMultiplexer();
        inputMultiplexer.addProcessor(stageSettings);
        inputMultiplexer.addProcessor(stageFill);
        Gdx.input.setInputProcessor(inputMultiplexer);
    }

    public void updateCamera() {
        // wait for our first picture if needed...
        while (ModelExecutor.msgFrameWideBuffer == null || ModelExecutor.frameWideData == null) {
            try {
                Thread.sleep(1);
            } catch (Exception e) { }
        }
        msgframeBuffer = ModelExecutor.msgFrameWideBuffer; // sh.recv(cameraBufferTopic).getWideRoadCameraBuffer();
        msgframeData = ModelExecutor.frameWideData; // sh.recv(cameraTopic).getWideRoadCameraState();
        imgBuffer = updateImageBuffer(msgframeBuffer, imgBuffer);
    }

    public void renderImage(boolean rgb) {
        if (!rgb) {
            if (nv12Renderer==null)
                nv12Renderer = new NV12Renderer(Camera.frameSize[0], Camera.frameSize[1]);
            nv12Renderer.render(imgBuffer);
        }
        else{
            pixelMap.setPixels(imgBuffer);
            texture.draw(pixelMap, 0, 0);
        }
    }

    public static float LatestvEgo;

    public void updateCarState() {
        Definitions.Event.Reader event = sh.recv(carStateTopic);
        LatestvEgo = event.getCarState().getVEgo();
        float vel = isMetric ? LatestvEgo * 3.6f : LatestvEgo * 2.237f;
        velocityLabel.setText(Integer.toString((int)vel));
    }

    public void updateControls() {
        controlState = sh.recv(controlsStateTopic).getControlsState();
        canErrCount = controlState.getCanErrorCounter();

        if (canErrCount != canErrCountPrev) {
            canMisses++;
            if (canMisses > 20)
                updateStatusLabel(statusLabelCan, "CAN\nOFFLINE", StatusColors.colorStatusCritical);
        }
        else{
            updateStatusLabel(statusLabelCan, "CAN\nONLINE", StatusColors.colorStatusGood);
            canMisses = 0;
        }
        canErrCountPrev = canErrCount;
    }

    public void updateModelOutputs(){
        Definitions.Event.Reader event = sh.recv(modelTopic);
        Definitions.LateralPlan.Reader latPlan = sh.recv("lateralPlan").getLateralPlan();
        PrimitiveList.Float.Reader pathpoints = latPlan.getDPathPoints();
        MsgModelDataV2.fillParsed(parsed, event.getModelV2(), true);

        try (MemoryWorkspace ws = Nd4j.getWorkspaceManager().getAndActivateWorkspace(wsConfig, "DrawUI")) {
            INDArray RtPath;
            INDArray Rt;
            Rt = Preprocess.eulerAnglesToRotationMatrix(-augmentRot.getFloat(0, 1), -augmentRot.getFloat(0, 2), -augmentRot.getFloat(0, 0), 0.0, false);
            RtPath = Preprocess.eulerAnglesToRotationMatrix(-augmentRot.getFloat(0, 1), -augmentRot.getFloat(0, 2), -augmentRot.getFloat(0, 0), 1.28, false);
            for (int i = 0; i< CommonModelF3.TRAJECTORY_SIZE; i++) {
                parsed.position.get(1)[i] = pathpoints.get(i);
                parsed.position.get(0)[i] = Math.max(parsed.position.get(0)[i], minZ);
                parsed.roadEdges.get(0).get(0)[i] = Math.max(parsed.roadEdges.get(0).get(0)[i], minZ);
                parsed.roadEdges.get(1).get(0)[i] = Math.max(parsed.roadEdges.get(1).get(0)[i], minZ);
            }
            path = Draw.getLaneCameraFrame(parsed.position, Camera.cam_intrinsics, RtPath, 0.9f);
            lane0 = Draw.getLaneCameraFrame(parsed.laneLines.get(0), Camera.cam_intrinsics, Rt, 0.07f);
            lane1 = Draw.getLaneCameraFrame(parsed.laneLines.get(1), Camera.cam_intrinsics, Rt, 0.05f);
            lane2 = Draw.getLaneCameraFrame(parsed.laneLines.get(2), Camera.cam_intrinsics, Rt, 0.05f);
            lane3 = Draw.getLaneCameraFrame(parsed.laneLines.get(3), Camera.cam_intrinsics, Rt, 0.07f);
            edge0 = Draw.getLaneCameraFrame(parsed.roadEdges.get(0), Camera.cam_intrinsics, Rt, 0.1f);
            edge1 = Draw.getLaneCameraFrame(parsed.roadEdges.get(1), Camera.cam_intrinsics, Rt, 0.1f);

            lead1s = Draw.getTriangleCameraFrame(parsed.leads.get(0), Camera.cam_intrinsics, Rt, leadDrawScale);
            //lead2s = Draw.getTriangleCameraFrame(parsed.leads.get(1), K, Rt, leadDrawScale);
            //lead3s = Draw.getTriangleCameraFrame(parsed.leads.get(2), K, Rt, leadDrawScale);
        }
    }

    public void handleSounds(Definitions.ControlsState.Reader controlState, AudibleAlert alert){
        if (alert == AudibleAlert.NONE) {
            if (controlState==null || controlsAlive == false)
                return;

            alert = controlState.getAlertSound();
        }

        if (currentAudibleAlert == alert)
            return;
        currentAudibleAlert = alert;

        for (AudibleAlert repeatAlerts : repeatingAlerts){
            soundAlerts.get(repeatAlerts).stop();
        }

        if (alert != AudibleAlert.NONE){
            Sound sound = soundAlerts.get(alert);
            if (ArrayUtils.contains(repeatingAlerts, alert))
                sound.loop();
            else
                sound.play();
        }
    }

    public void stopSounds(){
        for (AudibleAlert alert : soundAlerts.keySet()){
            soundAlerts.get(alert).stop();
        }
    }

    public void drawAlert(Definitions.ControlsState.Reader controlState, String forceAlert) {
        Definitions.ControlsState.AlertStatus alertStatus = null;
        Definitions.ControlsState.FlowpilotState state = null;
        if (forceAlert != null) {
            alertText1.setText(forceAlert);
            alertText2.setText(forceAlert);
            alertStatus = Definitions.ControlsState.AlertStatus.CRITICAL;
            state = Definitions.ControlsState.FlowpilotState.DISABLED;
        } else if (controlState != null) {
            alertText1.setText(controlState.getAlertText1().toString());
            alertText2.setText(controlState.getAlertText2().toString());
            alertStatus = controlState.getAlertStatus();
            state = controlState.getState();
            float maxVel = controlState.getVCruise();
            maxVel = isMetric ? maxVel * 3.6f : maxVel * 0.621371f;
            maxCruiseSpeedLabel.setText(Integer.toString(Math.round(maxVel)));
        }

        if (alertStatus==null || controlState==null) {
            status = UIStatus.STATUS_DISENGAGED;
        }
        else if (alertStatus == Definitions.ControlsState.AlertStatus.USER_PROMPT){
            status = UIStatus.STATUS_WARNING;
        }
        else if (alertStatus == Definitions.ControlsState.AlertStatus.CRITICAL){
            status = UIStatus.STATUS_ALERT;
        }
        else if (state == Definitions.ControlsState.FlowpilotState.PRE_ENABLED || state == Definitions.ControlsState.FlowpilotState.OVERRIDING){
            status = UIStatus.STATUS_OVERRIDE;
        }
        else{
            status = controlState.getEnabled() ? UIStatus.STATUS_ENGAGED : UIStatus.STATUS_DISENGAGED;
        }

        stageAlert.getViewport().apply();
        Gdx.gl.glEnable(GL20.GL_BLEND);
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, GL20.GL_ONE_MINUS_SRC_ALPHA);
        float borderShift = 0;
        if (infoTable.isVisible())
            borderShift = settingsBarWidth;
        appContext.shapeRenderer.setProjectionMatrix(cameraAlertBox.combined);
        appContext.shapeRenderer.begin(ShapeRenderer.ShapeType.Filled);
        colorBorder = statusColors.get(status);
        appContext.shapeRenderer.setColor(colorBorder[0] / 255f, colorBorder[1] / 255f, colorBorder[2] / 255f, 0.4f);

        if (alertText1.getText().toString().equals("") & alertText1.getText().toString().equals(""))
            appContext.shapeRenderer.rectLine(0, 0, uiWidth-borderShift ,0, borderWidth);
        else
            appContext.shapeRenderer.rectLine(0, 0, uiWidth-borderShift ,0, expandedBorderWidth);
        appContext.shapeRenderer.rectLine(uiWidth-borderShift ,0, uiWidth-borderShift, uiHeight, borderWidth);
        appContext.shapeRenderer.rectLine(uiWidth-borderShift, uiHeight, 0, uiHeight, borderWidth);
        appContext.shapeRenderer.rectLine(0, uiHeight,0, 0, borderWidth);
        appContext.shapeRenderer.end();
        Gdx.gl.glDisable(GL20.GL_BLEND);
    }


    public void drawStrip(INDArray[] strip, int[] color, float alpha, int drawLength, int res, int startOffset) {
        for (int i = startOffset; i < drawLength; i += res) {
            appContext.shapeRenderer.setColor(color[0] / 255f, color[1] / 255f, color[2] / 255f, alpha);
            appContext.shapeRenderer.triangle(strip[0].getFloat(i, 0), strip[0].getFloat(i, 1),
                    strip[1].getFloat(i, 0), strip[1].getFloat(i, 1),
                    strip[0].getFloat(i + res, 0), strip[0].getFloat(i + res, 1));
            appContext.shapeRenderer.triangle(strip[0].getFloat(i + res, 0), strip[0].getFloat(i + res, 1),
                    strip[1].getFloat(i, 0), strip[1].getFloat(i, 1),
                    strip[1].getFloat(i + res, 0), strip[1].getFloat(i + res, 1));
            alpha -= fadeStrength;
        }
    }

    public void drawLeadTriangle(INDArray leadTriangle, int[] color, float alpha){
        appContext.shapeRenderer.setColor(color[0] / 255f, color[1] / 255f, color[2] / 255f, alpha);
        appContext.shapeRenderer.triangle(leadTriangle.getFloat(0, 0), leadTriangle.getFloat(0, 1),
                leadTriangle.getFloat(1, 0), leadTriangle.getFloat(1, 1),
                leadTriangle.getFloat(2, 0), leadTriangle.getFloat(2, 1));
    }

    public int[] GetColorForProb(float prob) {
        if (prob > 0.5f) {
            prob = (prob - 0.5f) * 2f;
            return new int[] {
                Math.round(255 * (1f - prob)),
                255,
                0
            };
        } else {
            prob *= 2f;
            return new int[] {
                255,
                Math.round(255 * prob),
                0
            };
        }
    }

    public void drawModelOutputs() {
        appContext.shapeRenderer.begin(ShapeRenderer.ShapeType.Filled);
        appContext.shapeRenderer.setProjectionMatrix(cameraModel.combined);
        Gdx.gl.glEnable(Gdx.gl.GL_BLEND);
        Gdx.gl.glBlendFunc(Gdx.gl.GL_SRC_ALPHA, Gdx.gl.GL_ONE_MINUS_SRC_ALPHA);
        drawStrip(path, colorPath, 0.7f, defaultDrawLength, drawResolution, 0);
        drawStrip(lane0, GetColorForProb(parsed.laneLineProbs[0]), 0.9f, defaultDrawLength, drawResolution, 2);
        drawStrip(lane1, GetColorForProb(parsed.laneLineProbs[1]), 0.9f, defaultDrawLength, drawResolution, 2);
        drawStrip(lane2, GetColorForProb(parsed.laneLineProbs[2]), 0.9f, defaultDrawLength, drawResolution, 2);
        drawStrip(lane3, GetColorForProb(parsed.laneLineProbs[3]), 0.9f, defaultDrawLength, drawResolution, 2);
        drawStrip(edge0, colorEdges, 0.9f, defaultDrawLength, drawResolution, 2);
        drawStrip(edge1, colorEdges, 0.9f, defaultDrawLength, drawResolution, 2);

        if (parsed.leads.get(0).prob > minLeadProb)
            drawLeadTriangle(lead1s, colorLead, parsed.leads.get(0).prob);
        appContext.shapeRenderer.end();

        Gdx.gl.glDisable(Gdx.gl.GL_BLEND);
    }

    public void setUnits(){
        velocityUnitLabel.setText("mph");
    }

    @Override
    public void resize(int width, int height) {
        stageUI.getViewport().update(width, height);
        stageFill.getViewport().update(width, height);
        stageAlert.getViewport().update(width, height);
        stageSettings.getViewport().update(width, height);
    }

    @Override
    public void render(float delta) {
        Gdx.gl.glClearColor(0f, 0f, 0f, 1);
        Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT | GL20.GL_DEPTH_BUFFER_BIT | (Gdx.graphics.getBufferFormat().coverageSampling?GL20.GL_COVERAGE_BUFFER_BIT_NV:0));
        elapsed += Gdx.graphics.getDeltaTime();

        String noDebugInfo = null;
        if (appContext.isOnRoad && NoDebugMessagesWarning())
            noDebugInfo = "System Unresponsive!";

        if (appContext.isOnRoad) {
            offRoadRootTable.setVisible(false);

            stageFill.getViewport().apply();
            stageFill.act(delta);
            stageFill.draw();

            updateCamera();

            if (msgframeBuffer != null)
                renderImage(msgframeBuffer.getEncoding() == Definitions.FrameBuffer.Encoding.RGB);

            if (modelAlive)
                drawModelOutputs();

            // if we just got onroad, start by hiding the info on the side
            if (HideInfoTable) {
                setInfoTable(false);
                HideInfoTable = false;
            }

            setUnits();

            if (sh.updated(carStateTopic))
                updateCarState();

            drawAlert(controlState, noDebugInfo);

            stageUI.getViewport().apply();
            stageUI.draw();

            updateTempTimer -= delta;
            if (updateTempTimer <= 0f) {
                updateTempTimer = 1f;
                UpdateTemps();
                UpdateIP();
            }

            batch.begin();
            appContext.font.setColor(1, 1, 1, 1);
            appContext.font.draw(batch, "L1: " + Line1 + "\nL2: " + Line2,3,200);
            appContext.font.draw(batch, utils.F2 ? "Medium Model" : "Big Model", Gdx.graphics.getWidth() - 450f, 300f);
            appContext.font.draw(batch, "v" + VERSION + ", E" + CamExposure + ":" + currentExposureIndex, Gdx.graphics.getWidth() - 450f, 225f);
            appContext.font.draw(batch, tempStr + ", " + ModelExecutorF3.AvgIterationTime + "ms", Gdx.graphics.getWidth() - 450f, 150f);
            appContext.font.draw(batch, IPstring, Gdx.graphics.getWidth() - 450f, 75f);
            batch.end();
        }
        else{
            stopSounds();

            modelAlive = false;
            controlsAlive = false;
            setDefaultAlert();
            controlState = null;

            batch.begin();
            batch.setColor(1, 1, 1, 0.6f);
            batch.draw(getCurrentAnimation().getKeyFrame((float)elapsed), 0, 0, Gdx.graphics.getWidth(), Gdx.graphics.getHeight());
            batch.end();

            offRoadRootTable.setVisible(true);

            if (!infoTable.isVisible())
                infoTable.setVisible(true);

            // update offroad notifications
            if (Gdx.graphics.getFrameId()%10 == 0)
                updateOffroadNotifications();
        }

        stageSettings.getViewport().apply();
        stageSettings.act(delta);
        stageSettings.draw();

        if (sh.updated(calibrationTopic)) {
            Definitions.LiveCalibrationData.Reader liveCalib = sh.recv(calibrationTopic).getLiveCalibration();
            updateAugmentVectors(liveCalib);
        }

        if (sh.updated(modelTopic)) {
            updateModelOutputs();
            modelAlive = true;
        }

        if (sh.updated(controlsStateTopic)) {
            updateControls();
            controlsAlive = true;
        } else controlsAlive = false;

        handleSounds(controlState, noDebugInfo == null ? AudibleAlert.NONE : AudibleAlert.WARNING_IMMEDIATE);

        if (sh.updated(deviceStateTopic)) {
            updateDeviceState();
        }
    }

    @Override
    public void hide() {
        Gdx.input.setInputProcessor(null);
    }

    @Override
    public void dispose() {
        Gdx.input.setInputProcessor(null);
        stageFill.dispose();
        stageUI.dispose();
        sh.releaseAll();
    }
}
