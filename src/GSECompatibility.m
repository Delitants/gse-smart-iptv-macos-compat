#import <Cocoa/Cocoa.h>
#import <objc/runtime.h>
#import <mach-o/dyld.h>
#import <mach-o/loader.h>
#import <stdint.h>
static uintptr_t epgReturnAddress;
static void (*originalRemoval)(id,SEL,NSUInteger);
static void (*originalDoubleAction)(id,SEL,SEL);
static void (*originalDelegate)(id,SEL,id);

// Direct-distribution builds do not enqueue the vendor's delayed App Store
// receipt verifier. Its exact implementation address is checked before use.
static void directDistributionReceiptCallback(id object, SEL command) {}
BOOL GSEInstallDirectDistribution(Class delegate, uintptr_t expectedImplementation) {
    Method method=class_getInstanceMethod(delegate,sel_registerName("strategicPlace1"));
    if(!method || (uintptr_t)method_getImplementation(method)!=expectedImplementation)return NO;
    method_setImplementation(method,(IMP)directDistributionReceiptCallback);
    return YES;
}

// Only the known completion site in GSE 4.4 (52) may skip index zero on an empty queue.
void GSECheckedRemoval(NSMutableArray *array,NSUInteger index,uintptr_t caller) {
    if(caller==epgReturnAddress && index==0 && array.count==0) {
        NSLog(@"GSE Compatibility: ignored an already-drained EPG queue completion");
        return;
    }
    originalRemoval(array,@selector(removeObjectAtIndex:),index);
}
static void guardedRemoval(id array,SEL command,NSUInteger index) {
    GSECheckedRemoval(array,index,(uintptr_t)__builtin_return_address(0));
}
static void bindNavigationTarget(NSTableView *table) {
    if(table.target==nil && table.doubleAction==@selector(doubleClickedRow:) &&
       [(NSObject *)table.delegate respondsToSelector:table.doubleAction]) {
        table.target=(id)table.delegate;
    }
}
static void setDoubleAction(id table,SEL command,SEL action) {
    originalDoubleAction(table,command,action);
    bindNavigationTarget(table);
}
static void setDelegate(id table,SEL command,id delegate) {
    originalDelegate(table,command,delegate);
    bindNavigationTarget(table);
}
void GSEInstallCompatibility(uintptr_t knownEPGReturnAddress) {
    static dispatch_once_t once;
    dispatch_once(&once,^{
        epgReturnAddress=knownEPGReturnAddress;
        Class arrayClass=object_getClass([NSMutableArray array]);
        Method removal=class_getInstanceMethod(arrayClass,@selector(removeObjectAtIndex:));
        originalRemoval=(void *)method_setImplementation(removal,(IMP)guardedRemoval);
        Method action=class_getInstanceMethod([NSTableView class],@selector(setDoubleAction:));
        originalDoubleAction=(void *)method_setImplementation(action,(IMP)setDoubleAction);
        Method delegate=class_getInstanceMethod([NSTableView class],@selector(setDelegate:));
        originalDelegate=(void *)method_setImplementation(delegate,(IMP)setDelegate);
    });
}
__attribute__((constructor)) static void initializeGSECompatibility(void) {
    const struct mach_header_64 *header=(const void *)_dyld_get_image_header(0);
    if(!header || header->magic!=MH_MAGIC_64)return;
#if defined(__arm64__)
    if(header->cputype!=CPU_TYPE_ARM64)return;
    const unsigned char expected[16]={0x79,0xa5,0xcb,0x6c,0x81,0x84,0x3a,0xda,0x96,0x83,0xb3,0x5f,0xb3,0xda,0x39,0x0e};
    const uintptr_t returnOffset=0x1bada0;
    const uintptr_t receiptCallbackOffset=0x1fc97c;
#elif defined(__x86_64__)
    if(header->cputype!=CPU_TYPE_X86_64)return;
    const unsigned char expected[16]={0xdf,0x38,0x63,0x71,0xa7,0x7f,0x3d,0x79,0x91,0x66,0x4e,0x4b,0x9d,0xc4,0x7a,0x2a};
    const uintptr_t returnOffset=0x1c8cdd;
    const uintptr_t receiptCallbackOffset=0x20cc19;
#else
#error Unsupported architecture
#endif
    const struct load_command *command=(const void *)(header+1);
    BOOL matched=NO;
    for(uint32_t i=0;i<header->ncmds;i++) {
        if(command->cmd==LC_UUID && memcmp(((const struct uuid_command *)command)->uuid,expected,16)==0)matched=YES;
        command=(const void *)((const char *)command+command->cmdsize);
    }
    if(!matched)return;
    @autoreleasepool {
        GSEInstallCompatibility((uintptr_t)header+returnOffset);
        if(GSEInstallDirectDistribution(NSClassFromString(@"AppDelegate"),(uintptr_t)header+receiptCallbackOffset))
            NSLog(@"GSE Compatibility: direct distribution startup enabled");
        NSLog(@"GSE Compatibility: navigation binding and exact-site EPG guard installed");
    }
}
